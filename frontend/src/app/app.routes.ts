import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { authGuard } from './guards/auth-guard';
import { InteriorDashboardComponent } from './components/interior-dashboard/interior-dashboard';
import { CniDashboardComponent } from './components/cni-dashboard/cni-dashboard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'interior', component: InteriorDashboardComponent, canActivate: [authGuard] },
  { path: 'cni', component: CniDashboardComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'login' },
];