
export interface ServiceException extends Error {
  error_code: 'INTERNAL';
  error_name: string;
  parameters: {[key: string]: any};
}

export interface UnauthorizedError extends Error {
  error_code: 'UNAUTHORIZED';
  error_name: string;
  parameters: {[key: string]: any};
}

export interface NotFoundError extends Error {
  error_code: 'NOT_FOUND';
  error_name: string;
  parameters: {[key: string]: any};
}

export interface ConflictError extends Error {
  error_code: 'CONFLICT';
  error_name: string;
  parameters: {[key: string]: any};
}

export interface IllegalArgumentError extends Error {
  error_code: 'ILLEGAL_ARGUMENT';
  error_name: string;
  parameters: {[key: string]: any};
}
