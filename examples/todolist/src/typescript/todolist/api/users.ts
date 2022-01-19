import { Credentials, Service, ServiceException, StringType, StructType } from "@cytonic/runtime";

export interface User {
  id: string;
  email: string;
}

export const User_TYPE = new StructType<User>('User', {
  id: { type: new StringType() },
  email: { type: new StringType() },
});

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

const UsersService_TYPE: Service = {
  auth: {"type": "oauth2_bearer"},
  endpoints: {
    me: {
      method: 'GET',
      path: '/users/me',
      return: User_TYPE,
    },
    get_user: {
      method: 'GET',
      path: '/users/id/{user_id}',
      return: User_TYPE,
      args: {
        user_id: {
          type: new StringType(),
        },
      },
    },
  },
};
