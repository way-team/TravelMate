import { Component, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  Validators,
  EmailValidator
} from '@angular/forms';
import {
  NavController,
  MenuController,
  LoadingController,
  AlertController,
  Events
} from '@ionic/angular';
import { Language, Interest, UserProfile } from 'src/app/app.data.model';
import { DataManagement } from 'src/app/services/dataManagement';
import { TranslateService } from '@ngx-translate/core';
import { CookieService } from 'ngx-cookie-service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-register',
  templateUrl: './register.page.html',
  styleUrls: ['./register.page.scss']
})
export class RegisterPage implements OnInit {
  public onRegisterForm: FormGroup;
  username: string;
  password: string;
  confirmPassword: string;
  email: string;
  first_name: string;
  last_name: string;
  description: string;
  birthdate: string;
  gender: string;
  nationality: string;
  city: string;
  profesion: string;
  civilStatus: string;
  languages = [];
  languagesOptions: Language[];
  interests = [];
  interestsOptions: Interest[];
  profilePic: File = null;
  discoverPic: File = null;
  edit: string;
  isReady: boolean;

  constructor(
    public navCtrl: NavController,
    public menuCtrl: MenuController,
    public loadingCtrl: LoadingController,
    private formBuilder: FormBuilder,
    public dm: DataManagement,
    private translate: TranslateService,
    private cookieService: CookieService,
    public alertCtrl: AlertController,
    private activatedRoute: ActivatedRoute,
    public events: Events
  ) {
    this.listLanguages();
    this.listInterests();

    this.edit = this.activatedRoute.snapshot.paramMap.get('edit');
    if (this.edit === 'edit') {
      this.dm.getUserLogged(this.cookieService.get('token')).then(res => {
        this.email = res.email;
        this.first_name = res.first_name;
        this.last_name = res.last_name;
        this.description = res.first_name;
        this.birthdate = res.birthdate;
        this.profesion = res.profesion;
        this.civilStatus = res.civilStatus;
        this.gender = res.gender;
        this.nationality = res.nationality;
        this.city = res.city;
        res.languages.forEach(x => {
          var newLanguage: string;
          newLanguage = x;
          this.languages.push(newLanguage);
        });
        res.interests.forEach(x => {
          var newInterest: string;
          newInterest = x;
          this.interests.push(newInterest);
        });
        this.isReady = true;
      });
    } else {
      this.isReady = true;
    }
  }

  public listLanguages() {
    this.dm
      .listLanguages()
      .then(data => {
        this.languagesOptions = data;
      })
      .catch(error => {
        console.log(error);
      });
  }

  public listInterests() {
    this.dm
      .listInterests()
      .then(data => {
        this.interestsOptions = data;
      })
      .catch(error => {
        console.log(error);
      });
  }

  ionViewWillEnter() {
    if (this.edit !== 'edit') {
      this.menuCtrl.enable(false);
    } else {
      this.menuCtrl.enable(true);
    }
  }

  ngOnInit() {
    if (this.edit !== 'edit') {
      console.log('noo digas hola');
      this.onRegisterForm = this.formBuilder.group({
        username: [null, Validators.compose([Validators.required])],
        password: [null, Validators.compose([Validators.required])],
        confirmPassword: [null, Validators.compose([Validators.required])],
        email: [
          null,
          Validators.compose([Validators.required, Validators.email])
        ],
        first_name: [null, Validators.compose([Validators.required])],
        last_name: [null, Validators.compose([Validators.required])],
        profesion: [null, null],
        civilStatus: [null, Validators.compose([Validators.required])],
        description: [null, Validators.compose([Validators.required])],
        birthdate: [null, Validators.compose([Validators.required])],
        gender: [null, Validators.compose([Validators.required])],
        nationality: [null, Validators.compose([Validators.required])],
        city: [null, Validators.compose([Validators.required])],
        languages: [null, Validators.compose([Validators.required])],
        interests: [null, Validators.compose([Validators.required])]
      });
    } else {
      this.onRegisterForm = this.formBuilder.group({
        email: [
          null,
          Validators.compose([Validators.required, Validators.email])
        ],
        first_name: [null, Validators.compose([Validators.required])],
        last_name: [null, Validators.compose([Validators.required])],
        profesion: [null, null],
        civilStatus: [null, Validators.compose([Validators.required])],
        description: [null, Validators.compose([Validators.required])],
        birthdate: [null, Validators.compose([Validators.required])],
        gender: [null, Validators.compose([Validators.required])],
        nationality: [null, Validators.compose([Validators.required])],
        city: [null, Validators.compose([Validators.required])],
        languages: [null, Validators.compose([Validators.required])],
        interests: [null, Validators.compose([Validators.required])]
      });
    }
  }

  confirmPasswordValidation() {
    if (this.password === this.confirmPassword) {
      return true;
    } else {
      return false;
    }
  }

  public signUp() {
    let translation1: string = this.translate.instant(
      'REGISTER.HEADER_SUCCESS'
    );
    let translation2: string = this.translate.instant('REGISTER.SUCCESS');
    let translation3: string = this.translate.instant(
      'REGISTER.ERROR_USERNAME'
    );

    this.dm
      .register(
        this.username,
        this.password,
        this.email,
        this.first_name,
        this.last_name,
        this.description,
        this.birthdate.split('T')[0],
        this.profesion,
        this.civilStatus,
        this.gender,
        this.nationality,
        this.city,
        this.languages,
        this.interests,
        this.profilePic,
        this.discoverPic
      )
      .then(data => {
        this.showLoading();
        setTimeout(() => {
          this.alertCtrl
            .create({
              header: translation1,
              message: translation2,
              buttons: [
                {
                  text: 'Ok',
                  role: 'ok'
                }
              ]
            })
            .then(alertEl => {
              alertEl.present();
            });
          this.navCtrl.navigateForward('/');
          (this.username = ''),
            (this.password = ''),
            (this.confirmPassword = ''),
            (this.email = ''),
            (this.first_name = ''),
            (this.last_name = ''),
            (this.description = ''),
            (this.birthdate = ''),
            (this.gender = ''),
            (this.nationality = ''),
            (this.city = ''),
            (this.languages = []),
            (this.interests = []),
            (this.profilePic = null),
            (this.discoverPic = null);
        }, 1500);
      })
      .catch(error => {
        this.showLoading();
        setTimeout(() => {
          this.alertCtrl
            .create({
              header: 'Error',
              message: translation3,
              buttons: [
                {
                  text: 'Ok',
                  role: 'ok'
                }
              ]
            })
            .then(alertEl => {
              alertEl.present();
            });
        }, 1500);
      });
  }
  public editUser() {
    let translationHeader: string = this.translate.instant(
      'REGISTER.HEADER_SUCCESS_EDIT'
    );
    let translationMessage: string = this.translate.instant(
      'REGISTER.SUCCESS_EDIT'
    );

    this.dm
      .editUser(
        this.email,
        this.first_name,
        this.last_name,
        this.description,
        this.birthdate.split('T')[0],
        this.profesion,
        this.civilStatus,
        this.gender,
        this.nationality,
        this.city,
        this.languages,
        this.interests,
        this.profilePic,
        this.discoverPic
      )
      .then(data => {
        this.showLoading();
        setTimeout(() => {
          this.alertCtrl
            .create({
              header: translationHeader,
              message: translationMessage,
              buttons: [
                {
                  text: 'Ok',
                  role: 'ok'
                }
              ]
            })
            .then(alertEl => {
              alertEl.present();
            });

          this.events.publish('user:edited');
        }, 1500);
      })
      .catch(error => {});
  }
  showLoading() {
    const translation2: string = this.translate.instant('DISCOVER.WAIT');
    this.loadingCtrl
      .create({
        message: translation2,
        showBackdrop: true,
        duration: 1000
      })
      .then(loadingEl => {
        loadingEl.present();
      });
  }

  // // //
  goToLogin() {
    this.navCtrl.navigateRoot('/');
  }

  onProfilePicInputChange(file: File) {
    this.checkFileIsImage(file[0], 'profPic');
    this.profilePic = file[0];
  }

  onDiscoverPicInputChange(file: File) {
    this.checkFileIsImage(file[0], 'dicPic');
    this.discoverPic = file[0];
  }

  private checkFileIsImage(file: File, picture: string) {
    if (!(file.type.split('/')[0] == 'image')) {
      let translation1: string = this.translate.instant('REGISTER.IMAGE_ERROR');

      this.alertCtrl
        .create({
          header: translation1,
          buttons: [
            {
              text: 'Ok',
              role: 'ok'
            }
          ]
        })
        .then(alertEl => {
          alertEl.present();
        });

      if (picture == 'profPic') {
        this.profilePic = null;
        // Aunque de fallo de compilación, funciona
        (<HTMLInputElement>document.getElementById('procPic')).value = '';
      }

      if (picture == 'dicPic') {
        this.discoverPic = null;
        // Aunque de fallo de compilación, funciona
        (<HTMLInputElement>document.getElementById('dicoverPic')).value = '';
      }
    }
  }

  validateBirthdate() {
    const birthdate = new Date(this.birthdate);
    const today = new Date();

    if (birthdate > today) {
      return false;
    }
    return true;
  }

  private isAdult(): boolean {
    const today = new Date();
    const birthdate = new Date(this.birthdate);

    var edad = today.getFullYear() - birthdate.getFullYear();
    var m = today.getMonth() - birthdate.getMonth();

    if (m < 0 || (m === 0 && today.getDate() < birthdate.getDate())) {
      edad--;
    }

    return edad > 18;
  }

  changeLanguage(selectedValue: { detail: { value: string } }) {
    this.cookieService.set('lang', selectedValue.detail.value);
    this.translate.use(selectedValue.detail.value);
  }
}
