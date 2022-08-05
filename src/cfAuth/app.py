import os
SECRET_VALUE = os.environ.get('secret')
def handler(event, context):
    _res = {
      'isAuthorized': False,
    }
    if event['identitySource'][0] == SECRET_VALUE:
        _res['isAuthorized'] = True
    return _res