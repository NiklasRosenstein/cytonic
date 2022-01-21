
export class ServiceException {
  public error_code: string = 'INTERNAL';
  public error_name: string = 'Default:Internal';
  public constructor(public parameters: Parameters) { }
}

export class UnauthorizedError extends ServiceException {
  error_code = 'UNAUTHORIZED';
  error_name = 'Default:Unauthorized';
}

export class NotFoundError extends ServiceException {
  error_code = 'NOT_FOUND';
  error_name = 'Default:NotFound';
}

export class  ConflictError extends ServiceException {
  error_code = 'CONFLICT';
  error_name = 'Default:Conflict';
}

export class IllegalArgumentError extends ServiceException {
  error_code = 'ILLEGAL_ARGUMENT';
  error_name = 'Default:IllegalArgument';
}

export type Parameters = {[key: string]: any};
export type ErrorFactory = (params: Parameters) => ServiceException;
export type ErrorMapping = {[code: string]: ErrorFactory};

export const ERROR_MAPPING: ErrorMapping = {
  'UNAUTHORIZED': (p) => new UnauthorizedError(p),
  'NOT_FOUND': (p) => new NotFoundError(p),
  'CONFLICT': (p) => new ConflictError(p),
  'ILLEGAL_ARGUMENT': (p) => new IllegalArgumentError(p),
}

export function deserializeError(errorCode: string, errorName: string, parameters: Parameters): ServiceException {
  const handler = ERROR_MAPPING[errorCode];
  const exc = handler ? handler(parameters) : new ServiceException(parameters);
  exc.error_code = errorCode;
  exc.error_name = errorName;
  return exc;
}
