import { Credentials } from "@cytonic/runtime";
import { TodoListServiceAsync } from "../todolist";
import { UsersServiceAsync } from "../users";

const users = UsersServiceAsync.client({ baseURL: 'http://localhost:8000' });
const lists = TodoListServiceAsync.client({ baseURL: 'http://localhost:8000' });
const jw = Credentials.bearerToken('eY123.123');


test("test /users/me", async () => {
  expect(await users.me(jw))
    .toStrictEqual({ id: "0", email: "john.wick@example.org" });
});

test("test /users/id/0", async () => {
  expect(await users.get_user(jw, "0"))
    .toStrictEqual({ id: "0", email: "john.wick@example.org" });
});

test("test /lists", async () => {
  const todolists = await lists.get_lists(jw);
  expect(todolists.length).toEqual(2);
  expect(todolists[0].owner).toStrictEqual({ id: "0", email: "john.wick@example.org" });
  expect(todolists[1].owner).toStrictEqual({ id: "0", email: "john.wick@example.org" });
});
