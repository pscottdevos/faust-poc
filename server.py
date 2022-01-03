import asyncio
from collections import OrderedDict

import uvloop
from faust import App, Record
from faust.utils import json
from faust.web import View

from decorators.view_decorators import gathered_table_route


REST_LIST_STYLE = 'dict'


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


app = App('faust_poc',
    broker='kafka://localhost:9092',
    store='rocksdb://',
    partitions=5,
    internal=True,
    debug=True,
)


class KeyModel(Record):
    i: int

class ValueModel(Record):
    x: int
    y: str
    verb: str = ""

fpoc_topic = app.topic("fpoc-v2",
    key_type=KeyModel,
    key_serializer="json",
    value_type=ValueModel,
    partitions=5,
    internal=True,
)


sums_tables = app.Table('sums_tables', default=int)
counts_table = app.Table('counts_table', default=int)


@app.page('/debug')
async def get(self, request):
    data = {
        'table_keys': sorted(sums_tables.keys()),
        'table_meta': app.router.table_metadata('sums_tables'),
    }
    return self.json(data)


if REST_LIST_STYLE == 'dict':

    def marshal_list_view_output(table, _):
        return dict(sorted(table.items()))

    def merge(*bodies):
        data = {}
        for body in bodies:
            data.update(json.loads(body))
        return json.dumps(dict(sorted(data.items())))

elif REST_LIST_STYLE == 'list':

    def marshal_list_view_output(table, x_label):
        return [ {'y': y, x_label: x} for y, x in sorted(table.items()) ]

    def merge(*bodies):
        data = []
        for body in bodies:
            data += json.loads(body)
        return json.dumps(sorted(data, key=lambda d: str(d)))

else:
    raise ValueError(f"{REST_LIST_STYLE} must be one of 'dict' or 'list'")


@app.page('/counts')
class CountsView(View):

    @gathered_table_route(table=counts_table, merge=merge)
    async def get(self, request):
        return self.json(marshal_list_view_output(counts_table, 'count'))

@app.page('/counts/{y}')
class ValueView(View):

    @app.table_route(table=counts_table, match_info='y')
    async def get(self, request, y):
        return self.json(counts_table[y])

@app.page('/sums')
class ValuesView(View):

    @gathered_table_route(table=sums_tables, merge=merge)
    async def get(self, request):
        return self.json(marshal_list_view_output(sums_tables, 'x-sum'))

    async def post(self, request):
        data = await request.json()
        data["value"]["verb"] = "update"
        key = KeyModel(i=data["key"])
        value = ValueModel(**data["value"])
        try:
            result = await (await fpoc_topic.send(key=key, value=value))
        except TypeError as exc:
            return self.json({"errors": exc.args}, status=400)
        print("POST RESULT", result, result.__class__)
        return self.json(data)

@app.page('/sums/{y}')
class ValueView(View):

    @app.table_route(table=sums_tables, match_info='y')
    async def get(self, request, y):
        return self.json({y: sums_tables[y]})

    async def delete(self, request, y):
        key = KeyModel(i=0)
        value = ValueModel(x=sums_tables[y], y=y, verb="delete")
        try:
            result = await (await fpoc_topic.send(key=key, value=value))
        except TypeError as exc:
            return self.json({"errors": exc.args}, status=400)
        print(f'DELETE RESULT: {result} {result.__class__}')
        return self.json({"result": "OK"})


app.web.blueprints.add('/graph/', 'faust.web.apps.graph:blueprint')
app.web.blueprints.add('/router/', 'faust.web.apps.router:blueprint')
app.web.blueprints.add('/stats/', 'faust.web.apps.stats:blueprint')


@app.agent(fpoc_topic)
async def values_stream_agent(stream):
    async for key, value in stream.group_by(ValueModel.y).items():
        print(f'values_stream_agent', key, value)
        if value.verb == "update":
            sums_tables[value.y] += value.x
            counts_table[value.y] += 1
            yield {"updated": value.y}
        elif value.verb == "delete":
            del sums_tables[value.y]
            del counts_table[value.y]
            yield {"deleted": value.y}
        else:
            yield {"no action": value.y}
            print('NO ACTION: {value.verb}')
