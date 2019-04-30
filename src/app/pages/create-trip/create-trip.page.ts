import { Component, OnInit } from '@angular/core';
import { City } from '../../app.data.model';
import { DataManagement } from '../../services/dataManagement';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import {
  AlertController,
  NavController,
  LoadingController
} from '@ionic/angular';
import { ActivatedRoute } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-create-trip',
  templateUrl: './create-trip.page.html',
  styleUrls: ['./create-trip.page.scss']
})
export class CreateTripPage implements OnInit {
  public onCreateForm: FormGroup;
  id: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  trip_type: string = 'PUBLIC';
  city: City;
  image: File = null;
  error: string;
  cities: City[];
  userImage: File = null;
  privacyPolicites: boolean;
  validateDatesAttr: boolean = true;
  validateDatesBeforeToday: boolean = true;
  minDate: Date = new Date();

  constructor(
    public navCtrl: NavController,
    public dm: DataManagement,
    private formBuilder: FormBuilder,
    public alertCtrl: AlertController,
    private translate: TranslateService,
    private activatedRoute: ActivatedRoute,
    private loadingCtrl: LoadingController
  ) {
    this.listCities();
    this.id = this.activatedRoute.snapshot.paramMap.get('id');
    if (this.id) {
      const translation2: string = this.translate.instant('LOGIN.WAIT');
      this.loadingCtrl
        .create({
          message: translation2,
          showBackdrop: true,
          duration: 1000
        })
        .then(loadingEl => {
          loadingEl.present();
        });

      this.dm
        .getTripById(this.id)
        .then(response => {
          this.title = response['trip'].title;
          this.description = response['trip'].description;
          this.start_date = response['trip'].startDate;
          this.end_date = response['trip'].endDate;
          this.trip_type = response['trip'].tripType;
          this.city = new City();
          this.city.name = response['trip'].cities[0];
          this.city.id = this.cities.find(x => x.name == this.city.name)[0].id;
          this.userImage = response['trip'].userImage;
          loadingCtrl.dismiss();
        })
        .catch(_ => {});
    }
  }

  ngOnInit() {
    this.onCreateForm = this.formBuilder.group({
      title: [null, Validators.compose([Validators.required])],
      start_date: [null, Validators.compose([Validators.required])],
      end_date: [null, Validators.compose([Validators.required])],
      city: [null, Validators.compose([Validators.required])],
      userImage: [null, null]
    });
  }

  public createTrip() {
    const translation: string = this.translate.instant('TRIPS.ERROR');
    this.dm
      .createTrip(
        this.title,
        this.description === undefined ? '' : this.description,
        this.start_date.split('T')[0],
        this.end_date.split('T')[0],
        this.trip_type,
        this.city.id,
        this.userImage
      )
      .then(data => {
        this.navCtrl.navigateForward('/trips');
      })
      .catch(error => {
        this.alertCtrl
          .create({
            header: 'Error',
            message: translation,
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
      });
  }

  public editTrip() {
    console.log(typeof this.userImage);
    const translation: string = this.translate.instant('TRIPS.ERROR');
    this.dm
      .editTrip(
        this.id,
        this.title,
        this.description === undefined ? '' : this.description,
        this.start_date.split('T')[0],
        this.end_date.split('T')[0],
        this.trip_type,
        this.city.id,
        this.userImage
      )
      .then(data => {
        this.navCtrl.navigateForward('/trips');
      })
      .catch(error => {
        this.alertCtrl
          .create({
            header: 'Error',
            message: translation,
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
      });
  }

  public listCities() {
    this.dm
      .listCities()
      .then(data => {
        this.cities = data;
      })
      .catch(error => {
        console.log(error);
      });
  }
  goToPrivacyPolicies() {
    this.navCtrl.navigateForward('/gdpr');
  }

  validateDates() {
    const start = new Date(this.start_date);
    const end = new Date(this.end_date);

    if (start > end) {
      this.validateDatesAttr = false;
    } else {
      this.validateDatesAttr = true;
    }
    if (start < this.minDate) {
      this.validateDatesBeforeToday = false;
    } else {
      this.validateDatesBeforeToday = true;
    }
  }
  onFileInputChange(file: File) {
    this.userImage = file[0];
  }
}
