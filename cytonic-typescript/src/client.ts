
import axios, { Axios, AxiosRequestConfig, AxiosResponse, Method } from "axios";
import { Credentials } from "./auth";
import { Service, Endpoint, ParamKind, Authentication } from "./endpoint";
import { Locator } from "./types";


export interface ClientConfig {
  baseURL: string;
  timeout?: number;
  userAgent?: string;
}


export class CytonicClient {

  private axios: Axios;

  public constructor(private service: Service, config: ClientConfig) {
    this.axios = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      httpAgent: config.userAgent,
      httpsAgent: config.userAgent,
    });
  }

  public async request(endpointName: string, args: {[_: string]: any}): Promise<any> {
    const endpoint = this.service.endpoints[endpointName];
    if (endpoint === undefined) {
      throw new Error(`no such endpoint ${endpointName}`);
    }

    const request: AxiosRequestConfig<any> = {
      method: endpoint.method as Method,
      headers: {},
      params: {},
    };

    if (this.service.auth || endpoint.auth) {
      this.handleAuthArg(request, endpoint.auth, args.auth as Credentials);
    }


    const pathArgs: {[_: string]: any} = {};
    Object.entries(endpoint.args || {}).forEach(([argName, arg]) => {
      const serializedValue = arg.type.compose(new Locator([endpointName, argName]), args[argName]);
      switch (arg.kind) {
        case ParamKind.auth:
          throw new Error('auth args are not usually defined in the endpoint args list ...');
        case ParamKind.body:
          request.data = serializedValue;
          break;
        case ParamKind.cookie:
          throw new Error('cookie arguments are not currently supported');
        case ParamKind.header:
          request.headers![argName] = serializedValue;
          break;
        case ParamKind.path:
          pathArgs[argName] = serializedValue;
          break;
        case ParamKind.query:
          request.params![argName] = serializedValue;
          break;
        default:
          throw new Error(`unexpected argument ParamKind: ${arg.kind}`);
      }
    });

    // Render the path.
    request.url = renderPath(endpoint.path, pathArgs);

    console.log('request:', request);

    const response = await this.axios.request(request);

    console.log('response:', response);

    return null;
  }

  private handleAuthArg(request: AxiosRequestConfig<any>, endpointAuth: Authentication | undefined, cred: Credentials): void {
    if (cred === undefined) {
      throw new Error('missing "auth" argument');
    }
    throw new Error('not implemented');
  }

}


export function renderPath(template: string, args: {[_: string]: any}): string {
  Object.entries(args).forEach(([argName, arg]) => {
    if (arg instanceof Object) {
      arg = JSON.stringify(arg);
    }
    template = template.replace(`{${argName}}`, '' + arg);
  });
  return template;
}


export function createAsyncClient<T>(service: Service, config: ClientConfig): T {
  const client = new CytonicClient(service, config);
  const createEndpointFunction = (endpointName: string, endpoint: Endpoint) => {
    function handler(): Promise<any> {
      let expectedArgCount = endpoint.args === undefined ? 0 : Object.entries(endpoint.args).length;
      if (service.auth || endpoint.auth) expectedArgCount++;
      if (arguments.length === expectedArgCount) {
        throw new Error(`endpoint ${endpointName} expected ${expectedArgCount} argument(s) but got ${arguments.length}`);
      }
      let idx = 0;
      const args: {[_: string]: any} = {};
      const callArgs = arguments;
      if (service.auth || endpoint.auth) {
        args['auth'] = callArgs[idx++];
      }
      (endpoint.args_ordering || []).forEach(argName => {
        args[argName] = callArgs[idx++];
      });
      return client.request(endpointName, args);
    };
    return handler;
  };
  const instance: {[_: string]: any} = {};
  Object.entries(service.endpoints).forEach(([endpointName, endpoint]) => {
    instance[endpointName] = createEndpointFunction(endpointName, endpoint);
  });
  return instance as unknown as T;
}
