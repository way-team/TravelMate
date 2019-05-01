import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';

@Injectable()
export class ConfigService {
  constructor() {}

  public config() {
    let urlPrefix = 'http://192.168.1.135:8000/';
    let urlPrefixLocalhost = 'http://localhost:8000/';
    let urlAPI = '';
    if (environment.production) {
      urlPrefix = 'https://travel-mate-server-s3.herokuapp.com/';
      urlPrefixLocalhost = 'https://travel-mate-server-s3.herokuapp.com/';
      urlAPI = '';
    }
    // pathFiles for Storage provider
    let pathFiles = '/assets/storageFiles';
    // myCustomVars
    let myCustomVars1 = 123;
    let myCustomVars2 = 456;
    return {
      restUrlPrefix: urlPrefix + urlAPI,
      restUrlPrefixLocalhost: urlPrefixLocalhost + urlAPI,
      destPathFiles: pathFiles,
      myCustomVars1: myCustomVars1,
      myCustomVars2: myCustomVars2
    };
  }
}
