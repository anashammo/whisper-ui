import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Feature Components
import { UploadComponent } from './features/upload/upload.component';
import { TranscriptionComponent } from './features/transcription/transcription.component';
import { HistoryComponent } from './features/history/history.component';

// Shared Components
import { PopupComponent } from './shared/components/popup/popup.component';
import { FooterComponent } from './shared/components/footer/footer.component';

// Core Services
import { ApiService } from './core/services/api.service';
import { TranscriptionService } from './core/services/transcription.service';

// Shared Services
import { PopupService } from './shared/services/popup.service';

@NgModule({
  declarations: [
    AppComponent,
    UploadComponent,
    TranscriptionComponent,
    HistoryComponent,
    PopupComponent,
    FooterComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    CommonModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [
    ApiService,
    TranscriptionService,
    PopupService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
