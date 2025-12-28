import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UploadComponent } from './features/upload/upload.component';
import { TranscriptionComponent } from './features/transcription/transcription.component';
import { HistoryComponent } from './features/history/history.component';

const routes: Routes = [
  { path: '', component: UploadComponent },
  { path: 'transcription/:id', component: TranscriptionComponent },
  { path: 'history', component: HistoryComponent },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
