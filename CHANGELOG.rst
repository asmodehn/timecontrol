Changelog
=========


0.2.2 (2019-11-23)
------------------
- Adapting our async sleep to routine or coroutine sleepers. [AlexV]
- Quickfix patching asyncio.sleep not awaited. [AlexV]
- Added few comments in setup.py. [AlexV]


0.2.1 (2019-11-21)
------------------
- V0.2.1. [AlexV]
- Adding aiounittest as requirement. [AlexV]
- V0.2.1. [AlexV]
- Fixing command's sleeper argument so we do not override default by
  passing None. [AlexV]
- Fixing underlimiteer so it forwards the async nature of the wrapped
  callable... [AlexV]
- Small refctor to make the async command runner a specialization of the
  sync one. [AlexV]
- Making command async tests pass. [AlexV]
- Adding test for async command. [AlexV]
- Adding gitignore. [AlexV]
- Merge pull request #3 from asmodehn/version. [AlexV]

  Version
- Adding envrc for ease of use. adding various dev dependencies. [AlexV]
- V0.1.1. [AlexV]
- Fixing main in self tests to remove function tests. [AlexV]
- Fixing version file path also removing underlimit test for function.
  [AlexV]
- V0.1.1. [AlexV]
- Adding package managemnt code... [AlexV]
- Removing function feature. not ready for prime time just yet. [AlexV]
- Now command supporting to decorate a class. [AlexV]
- Merge pull request #1 from asmodehn/command_method_fix. [AlexV]

  Command method fix
- Removing wrapt import, more confusing than helping. [AlexV]
- Refactor CommandRunner and Runner. fixing Command to allow passing
  sleeper dependency. [AlexV]
- Quick fix of Command to work on instance methods. [AlexV]
- Adding badge. [AlexV]
- Adding test for underlimited function and command. [AlexV]
- Adding tests for command, function and eventlog. [AlexV]
- Playing around with function and command concepts related to time...
  [AlexV]
- Adding main module for tests. [AlexV]
- Adding empty test folder. [AlexV]
- Adding overlimiter tests. [AlexV]
- Adding travis config. [AlexV]
- Adding tests for underlimiter. [AlexV]
- Adding basic limiters and beginning of a project structure. [AlexV]
- Initial commit. [AlexV]


