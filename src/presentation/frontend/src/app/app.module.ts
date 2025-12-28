import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Feature Components
import { UploadComponent } from './features/upload/upload.component';
import { TranscriptionComponent } from './features/transcription/transcription.component';
import { HistoryComponent } from './features/history/history.component';

// Core Services
import { ApiService } from './core/services/api.service';
import { TranscriptionService } from './core/services/transcription.service';

@NgModule({
  declarations: [
    AppComponent,
    UploadComponent,
    TranscriptionComponent,
    HistoryComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [
    ApiService,
    TranscriptionService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
