import { User } from "./users";
import { Credentials, ServiceException } from "@cytonic/runtime";

export interface TodoList {
  id: string;
  name: string;
  owner: User;
  created_at: Date;
}

export interface TodoItem {
  text: string;
  created_at: Date;
}

export class TodoListNotFoundError extends ServiceException {
  public constructor(public list_id: string) { super(); }
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
