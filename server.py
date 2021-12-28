from collections import OrderedDict

from faust import App, Record
from faust.web import View


app = App('faust_poc',
    broker='kafka://localhost:9092',
    store='memory://',
    partitions=5,
    internal=True,
    debug=True,
)


class KeyModel(Record):
    i: int


class ValueModel(Record):
    x: int
    y: str


fpoc_topic = app.topic("fpoc",
    key_type=KeyModel,
    key_serializer="json",
    value_type=ValueModel,
    partitions=5,
    internal=True,
)


values_table = app.Table('values_table', default=int)


@app.page('/values')
class ValuesView(View):

    async def get(self, request, ):
        return self.json( OrderedDict(sorted(values_table.items())) )

    async def post(self, request):
        data = await request.json()
        try:
            result = await fpoc_topic.send(
                key=KeyModel(i=data["key"]), value=ValueModel(**data["value"])
            )
        except TypeError as exc:
            return self.json({"errors": exc.args}, status=400)
        return self.json(data)

@app.page('/values/{y}')
@app.table_route(table=values_table, match_info='y')
class ValueView(View):

    async def get(self, request, y):
        return self.json(values_table[y])

    async def delete(self, request, y):
        value = self.json(values_table[y])
        del values_table[y]
        return value


app.web.blueprints.add('/graph/', 'faust.web.apps.graph:blueprint')
app.web.blueprints.add('/router/', 'faust.web.apps.router:blueprint')
app.web.blueprints.add('/stats/', 'faust.web.apps.stats:blueprint')


@app.agent(fpoc_topic)
async def values_stream_agent(values_stream):
    async for key, value in values_stream.group_by(ValueModel.y).items():
        print('values_stream_agent', key, value)
        values_table[value.y] += value.x
