import importlib


def test_v6_package_api_imports_without_fastapi_response_model_error() -> None:
    module = importlib.import_module("app.api.v6_app_flow")

    download_routes = [
        route
        for route in module.router.routes
        if getattr(route, "path", "") == "/runs/{run_id}/operator/v6/package/download"
    ]

    assert len(download_routes) == 1
    assert download_routes[0].response_model is None
