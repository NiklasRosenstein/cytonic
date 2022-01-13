
export interface BearerToken {
  type: 'BearerToken';
  value: string;
}

export interface BasicAuth {
  type: 'BasicAuth';
  username: string;
  password: string;
}

export class Credentials {
  public constructor(
    public value: BearerToken | BasicAuth) {}

  public get_bearer_token(): string {
    if (this.value.type !== 'BearerToken') {
      throw new Error("not a bearer token in credentials");
    }
    return this.value.value;
  }

  public get_basic_auth(): BasicAuth {
    if (this.value.type !== 'BasicAuth') {
      throw new Error("not a basic auth in credentials");
    }
    return this.value;
  }
}
