import { User, User_TYPE } from "./users";
import { Credentials, DatetimeType, ListType, ParamKind, Service, ServiceException, StringType, StructType } from "@cytonic/runtime";

export interface TodoList {
  id: string;
  name: string;
  owner: User;
  created_at: Date;
}

export const TodoList_TYPE = new StructType<TodoList>('TodoList', {
  id: { type: new StringType() },
  name: { type: new StringType() },
  owner: { type: User_TYPE },
  created_at: { type: new DatetimeType() },
});

export interface TodoItem {
  text: string;
  created_at: Date;
}

export const TodoItem_TYPE = new StructType<TodoItem>('TodoItem', {
  text: { type: new StringType() },
  created_at: { type: new DatetimeType() },
});

export interface TodoListNotFoundError extends ServiceException {
  error_name: 'TodoList:TodoListNotFound'
  parameters: {
    list_id: string,
  }
}

/**
 * A simple todo list API.
 */
export interface TodoListServiceAsync {
  get_lists(auth: Credentials): Promise<TodoList[]>;
  get_items(auth: Credentials, list_id: string): Promise<TodoItem[]>;
  set_items(auth: Credentials, list_id: string, items: TodoItem[]): Promise<void>;
}

/**
 * A simple todo list API.
 */
export interface TodoListServiceBlocking {
  get_lists(auth: Credentials): TodoList[];
  get_items(auth: Credentials, list_id: string): TodoItem[];
  set_items(auth: Credentials, list_id: string, items: TodoItem[]): null;
}

const TodoListService_TYPE: Service = {
  auth: {"type": "oauth2_bearer"},
  endpoints: {
    get_lists: {
      method: 'GET',
      path: '/lists',
      return: new ListType(TodoList_TYPE),
    },
    get_items: {
      method: 'GET',
      path: '/lists/{list_id}/items',
      return: new ListType(TodoItem_TYPE),
      args: {
        list_id: {
          kind: ParamKind.path,
          type: new StringType(),
        },
      },
    },
    set_items: {
      method: 'POST',
      path: '/lists/{list_id}/items',
      args: {
        list_id: {
          kind: ParamKind.path,
          type: new StringType(),
        },
        items: {
          kind: ParamKind.body,
          type: new ListType(TodoItem_TYPE),
        },
      },
    },
  },
};
