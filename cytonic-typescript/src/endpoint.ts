import { TypeDescriptor } from "./types";

export enum ParamKind {
  auth = 'auth',
  body = 'body',
  cookie = 'cookie',
  header = 'header',
  path = 'path',
  query = 'query',
}


export interface OAuth2Bearer {
  type: 'oauth2_bearer',
  header_name?: string,
}


export interface BasicAuth {
  type: 'basic',
}


export interface NoAuth {
  type: 'none',
}


export type Authentication = OAuth2Bearer | BasicAuth | NoAuth;


export interface Argument {
  type: TypeDescriptor,
  kind: ParamKind,
}


export interface Endpoint {
  method: string,
  path: string,
  auth?: Authentication,
  args?: {[_: string]: Argument},
  return?: TypeDescriptor,
}


export interface Service {
  auth?: Authentication,
  endpoints: {[_: string]: Endpoint},
}