# Change Log
All notable changes to this project will be documented in this file.

## 0.3.0 - 2019-09-25
### Added
- No change.

### Changed
- Updated Python 3.7 support.
- Updated license to reflect new project institution.
- Updated pyzmq dependency to allow >=14.3

### Removed
- No change.


## 0.2.0 - 2016-08-26
### Added
- Error handling has been cleaned up to make it easier to provide an easier mechanism for globally processing errors
and returning a consistently formatted response. Specifically, the handle_errors() function was added to utils.py.

### Changed
- THe AgaveflaskError classes were updated to contain message and code data about the error.

### Removed
- The APIException class has been removed in favor of the AgaveflaskError classes.


## 0.1.0 - 2016-08-26
### Added
- Initial release of modules: auth, config, errors, store and utils.

### Changed
- No change.

### Removed
- No change.

