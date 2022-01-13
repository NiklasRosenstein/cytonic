import { Credentials, ServiceException } from "@cytonic/runtime";

export interface User {
  id: string;
  email: string;
}

export interface UserNotFoundError extends ServiceException {
  error_name: 'Users:UserNotFound'
  parameters: {
    user_id: string,
  }
}

/**
 * User management service.
 */
export interface UsersServiceAsync {
  me(auth: Credentials): Promise<User>;
  get_user(auth: Credentials, user_id: string): Promise<User>;
}

/**
 * User management service.
 */
export interface UsersServiceBlocking {
  me(auth: Credentials): User;
  get_user(auth: Credentials, user_id: string): User;
}
