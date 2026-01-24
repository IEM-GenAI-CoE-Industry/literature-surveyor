import traceback

try:
    import api_services
    routes = getattr(api_services, "api_router", None)
    print("api_services module:", getattr(api_services, "__file__", "(built-in)") )
    if routes is None:
        print("api_services imported but no 'api_router' found.")
    else:
        print("api_router routes:")
        try:
            print([r.path for r in routes.routes])
        except Exception as e:
            print("Failed to enumerate routes:", e)
except Exception:
    print("Import failed:")
    traceback.print_exc()
