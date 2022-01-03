from functools import wraps
from typing import Any, Callable

from faust.types.tables import CollectionT
from faust.types.web import Request, Response, ViewHandlerFun
from faust import web
from yarl import URL


prevent_forwarding_qs = '-no-merge'

def gathered_table_route(table: CollectionT, merge: Callable[..., str]):
    """Decorate view method to gather results across workers"""
    def _decorator(fun: ViewHandlerFun) -> ViewHandlerFun:
        app = table.app
        router = app.router

        @wraps(fun)
        async def get(view: web.View, request: Request,
                      *args: Any, **kwargs: Any) -> Response:
            prevent_merge = prevent_forwarding_qs in request.query
            urls = [
                URL(url) for url in app.router.table_metadata(table.name).keys()
            ]
            bodies = []
            local_response = None
            for url in urls:
                dest_ident = (host, port) = router._urlident(url)
                if dest_ident == router._urlident(app.conf.canonical_url):
                    local_response = await fun(view, request, *args, **kwargs)
                    if prevent_merge:
                        return local_response
                    else:
                        bodies.append(local_response.text)
                elif not prevent_merge:
                    routed_url = (request.url
                        .with_host(host)
                        .with_port(port)
                        .with_query(prevent_forwarding_qs)
                    )
                    async with app.http_client.get(routed_url) as response:
                        if not local_response:
                            local_response = response
                        bodies.append(await (response.text()))
            merged_response = merge(*bodies)
            return view.text(merged_response, content_type=local_response.content_type)

        return get

    return _decorator
