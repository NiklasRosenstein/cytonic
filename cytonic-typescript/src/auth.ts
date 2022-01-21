
export interface BearerToken {
  type: 'BearerToken';
  value: string;
}

export interface BasicAuth {
  type: 'BasicAuth';
  username: string;
  password: string;
}

export interface None {
  type: 'None'
}

export class Credentials {
  public constructor(
    public value: BearerToken | BasicAuth | None) {}

  public static bearerToken(token: string) {
    return new Credentials({type: 'BearerToken', value: token});
  }

  public static basicAuth(username: string, password: string) {
    return new Credentials({type: 'BasicAuth', username, password});
  }

  public static none() {
    return new Credentials({type: 'None'});
  }

  public type(): 'BearerToken' | 'BasicAuth' | 'None' {
    return this.value.type;
  }

  public isBearerToken(): boolean {
    return this.value.type == 'BearerToken';
  }

  public isBasicAuth(): boolean {
    return this.value.type == 'BasicAuth';
  }

  public isNone(): boolean {
    return this.value.type == 'None';
  }

  public getBearerToken(): string {
    if (this.value.type !== 'BearerToken') {
      throw new Error("not a bearer token in credentials");
    }
    return this.value.value;
  }

  public getBasicAuth(): BasicAuth {
    if (this.value.type !== 'BasicAuth') {
      throw new Error("not a basic auth in credentials");
    }
    return this.value;
  }
}
