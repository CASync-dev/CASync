from flask import abort, current_app, request
from app.testing import testing

# This route is only added to the app if the app is run in testing.

@testing.route('/shutdown')
def server_shutdown():
    print("hello!")
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'