import { Decimal as _Decimal } from "decimal.js";
import moment from "moment";


export class Locator {
  public constructor(public path: (string | number)[]) {}

  public push(value: string | number): Locator {
    return new Locator([...this.path, value]);
  }

  public error(message: string): Error {
    return new Error(`${this.toString()}: {message}`);
  }

  public toString(): string {
    return ['$', ...this.path].join('.');
  }
}


export interface TypeDescriptor {
  name: string;
  extract(locator: Locator, value: any): any;
  compose(locator: Locator, value: any): any;
  toString(): string;
}


export class StringType implements TypeDescriptor {

  public name = 'string';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'string') {
      throw locator.error(`expected type "string", got "${typeof value}"`);
    }
    return value;
  }

  public compose(locator: Locator, value: any) {
    return this.extract(locator, value);
  }

  public toString(): string {
    return this.name;
  }

}


export class IntegerType implements TypeDescriptor {

  public name = 'integer';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'number') {
      throw locator.error(`expected type "number" for integer, got "${typeof value}"`);
    }
    if (Math.round(value) !== value) {
      throw locator.error(`"${value}" is not a round number`);
    }
    return value;
  }

  public compose(locator: Locator, value: any) {
    return this.extract(locator, value);
  }

  public toString(): string {
    return this.name;
  }
}


export class DoubleType implements TypeDescriptor {

  public name = 'double';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'number') {
      throw locator.error(`expected type "number" for double, got "${typeof value}"`);
    }
    return value;
  }

  public compose(locator: Locator, value: any) {
    return this.extract(locator, value);
  }

  public toString(): string {
    return this.name;
  }
}


export class DecimalType implements TypeDescriptor {

  public name = 'decimal';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'number' && typeof value !== 'string') {
      throw locator.error(`expected type "number" or "string" for decimal, got "${typeof value}"`);
    }
    return new _Decimal(value);
  }

  public compose(locator: Locator, value: any) {
    return (value as _Decimal).toString();
  }

  public toString(): string {
    return this.name;
  }
}


export class BooleanType implements TypeDescriptor {

  public name = 'boolean';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'boolean') {
      throw locator.error(`expected type "boolean", got "${typeof value}"`);
    }
    return value;
  }

  public compose(locator: Locator, value: any) {
    return this.extract(locator, value);
  }

  public toString(): string {
    return this.name;
  }
}


export class DatetimeType implements TypeDescriptor {

  public name = 'datetime';

  public extract(locator: Locator, value: any) {
    if (typeof value !== 'string') {
      throw locator.error(`expected type "string" for datetime, got "${typeof value}"`);
    }
    return moment(value, moment.ISO_8601);
  }

  public compose(locator: Locator, value: any) {
    return (value as moment.Moment).toISOString();
  }

  public toString(): string {
    return this.name;
  }
}


export class ListType implements TypeDescriptor {

  public name = 'list';

  public constructor(public itemType: TypeDescriptor) {}

  public extract(locator: Locator, value: any) {
    if (!Array.isArray(value)) {
      throw locator.error(`expected type "array" for list, got "${typeof value}"`);
    }
    return value.map((v, i) => this.itemType.extract(locator.push(i), v));
  }

  public compose(locator: Locator, value: any) {
    if (!Array.isArray(value)) {
      throw locator.error(`expected type "array" for list, got "${typeof value}"`);
    }
    return value.map((v, i) => this.itemType.compose(locator.push(i), v));
  }

  public toString(): string {
    return `${this.name}<${this.itemType.toString()}>`;
  }
}


export class SetType implements TypeDescriptor {

  public name = 'set';

  public constructor(public itemType: TypeDescriptor) {}

  public extract(locator: Locator, value: any) {
    if (!Array.isArray(value)) {
      throw locator.error(`expected type "array" or "Set" for set, got "${typeof value}"`);
    }
    return new Set(value.map((v, i) => this.itemType.extract(locator.push(i), v)));
  }

  public compose(locator: Locator, value: any) {
    value = new Set<any>(value);
    return [...value].map((v, i) => this.itemType.compose(locator.push(i), v));
  }

  public toString(): string {
    return `${this.name}<${this.itemType.toString()}>`;
  }
}


export class MapType implements TypeDescriptor {

  public name = 'map';

  public constructor(public keyType: TypeDescriptor, public valueType: TypeDescriptor) {}

  public extract(locator: Locator, value: any) {
    let entries: [string, any][];
    if (value instanceof Map) {
      entries = Array.from(value.entries());
    }
    else if (value instanceof Object) {
      entries = Array.from(Object.entries(value));
    }
    else {
      throw locator.error(`expected type "Map" or "Object" for map, got "${typeof value}"`);
    }
    return new Map(entries.map(([k, v], i) => [
      this.keyType.extract(locator.push(i), k),
      this.valueType.extract(locator.push(i), v)
    ]));
  }

  public compose(locator: Locator, value: any) {
    let entries: [string, any][];
    if (value instanceof Map) {
      entries = Array.from(value.entries());
    }
    else if (value instanceof Object) {
      entries = Array.from(Object.entries(value));
    }
    else {
      throw locator.error(`expected type "Map" or "Object" for map, got "${typeof value}"`);
    }
    return new Map(entries.map(([k, v], i) => [
      this.keyType.compose(locator.push(i), k),
      this.valueType.compose(locator.push(i), v)
    ]));
  }

  public toString(): string {
    return `${this.name}<${this.keyType.toString()}, ${this.valueType.toString()}>`;
  }
}


export class OptionalType implements TypeDescriptor {

  public name = 'optional';

  public constructor(public innerType: TypeDescriptor) {}

  public extract(locator: Locator, value: any) {
    if (value === undefined || value === null) {
      return undefined;
    }
    return this.innerType.extract(locator, value);
  }

  public compose(locator: Locator, value: any) {
    if (value === undefined || value === null) {
      return undefined;
    }
    return this.innerType.compose(locator, value);
  }

  public toString(): string {
    return `${this.name}<${this.innerType.toString()}>`;
  }
}


export interface StructField {
  type: TypeDescriptor,
}


export class StructType<T> implements TypeDescriptor {

  public constructor(public name: string, public fields: {[_: string]: StructField}) {}

  public extract(locator: Locator, value: any): T {
    const result: {[_: string]: any} = {};
    Object.entries(this.fields).forEach(([fieldName, field]) => {
      result[fieldName] = field.type.extract(locator.push(fieldName), value[fieldName]);
    });
    return result as T;
  }

  public compose(locator: Locator, value: T): any {
    const record: {[_: string]: any} = {};
    Object.entries(this.fields).forEach(([fieldName, field]) => {
      record[fieldName] = field.type.compose(locator.push(fieldName), (value as any)[fieldName]);
    });
    return record;
  }

}
