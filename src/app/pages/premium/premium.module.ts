import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Routes, RouterModule } from '@angular/router';
import{TranslateModule} from '@ngx-translate/core';
import { IonicModule } from '@ionic/angular';

import { PremiumPage } from './premium.page';

const routes: Routes = [
  {
    path: '',
    component: PremiumPage
  }
];

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    TranslateModule,
    RouterModule.forChild(routes)
  ],
  declarations: [PremiumPage]
})
export class PremiumPageModule {}
