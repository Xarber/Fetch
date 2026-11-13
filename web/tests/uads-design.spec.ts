// SPDX-License-Identifier: AGPL-3.0-only
import {test,expect} from '@playwright/test';

test('landing, setup guide, icons, contrast and private workspace remain distinct',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/?welcome');
 await expect(page.getByRole('heading',{name:'Keep something worth keeping.'})).toBeVisible();
 await expect(page.getByText('no signed app release is available yet',{exact:false})).toBeVisible();
 await expect(page.getByRole('img',{name:/Fetch browser dashboard/})).toBeVisible();
 await page.screenshot({path:'docs/reports/landing-desktop.png',fullPage:true});
 await page.getByRole('link',{name:'Open your workspace'}).click();
 await expect(page.getByRole('heading',{name:'Good media. Yours to keep.'})).toBeVisible();
 await expect(page.locator('[data-view=overview] svg')).toHaveCount(1);
 const contrast=await page.locator('.source-note').evaluate(el=>{
  const parse=(v:string)=>v.match(/[\d.]+/g)!.slice(0,3).map(Number);
  const luminance=(rgb:number[])=>rgb.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i]!,0);
  const foreground=luminance(parse(getComputedStyle(el).color));
  const background=luminance(parse(getComputedStyle(document.querySelector('.download-card')!).backgroundColor));
  return (Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05);
 });expect(contrast).toBeGreaterThanOrEqual(4.5);
 await page.getByRole('button',{name:'Connect server',exact:true}).click();
 await expect(page.locator('#login-dialog')).toBeVisible();
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await page.getByRole('link',{name:'Setup guide',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Start on your own terms.'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.goto('/?welcome');
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'docs/reports/landing-mobile.png',fullPage:true});
 expect(errors).toEqual([]);
});

test('reduced motion, keyboard interaction and offline landing work in dark mode',async({page,context})=>{
 await page.emulateMedia({reducedMotion:'reduce',colorScheme:'dark'});
 await page.goto('/#app');
 await page.getByRole('button',{name:'Connect server',exact:true}).focus();
 await page.keyboard.press('Enter');
 await expect(page.locator('#login-dialog')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.dataset.input)).toBe('keyboard');
 await page.keyboard.press('Escape');
 await expect(page.locator('#login-dialog')).not.toBeVisible();
 await page.goto('/?welcome');
 expect(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
 await page.evaluate(async()=>{await navigator.serviceWorker.ready;});
 await context.setOffline(true);await page.reload();
 await expect(page.getByRole('heading',{name:'Keep something worth keeping.'})).toBeVisible();
 await context.setOffline(false);
});


test('root introduction is remembered and returning preserves unsaved input', async ({page}) => {
 await page.goto('/');
 await expect(page.getByRole('heading', {name: 'Keep something worth keeping.'})).toBeVisible();
 await page.getByRole('link', {name: 'Open your workspace'}).click();
 await page.goBack();
 await expect(page.getByRole('heading', {name: 'Keep something worth keeping.'})).toBeVisible();
 await page.goForward();
 await page.locator('#source-url').fill('https://example.com/unsaved');
 await page.getByRole('link', {name: 'Fetch home', exact: true}).click();
 await expect(page.getByRole('heading', {name: 'Keep something worth keeping.'})).toBeVisible();
 await page.goBack();
 await expect(page.locator('#source-url')).toHaveValue('https://example.com/unsaved');
 await page.goForward();
 await expect(page.getByRole('heading', {name: 'Keep something worth keeping.'})).toBeVisible();
 await page.getByRole('link', {name: 'Open your workspace'}).click();
 await expect(page.locator('#source-url')).toHaveValue('https://example.com/unsaved');
 await page.goto('/');
 await expect(page.getByRole('heading', {name: 'Good media. Yours to keep.'})).toBeVisible();
 await page.goto('/#queue');
 await expect(page.getByRole('heading', {name: 'Download queue'})).toBeVisible();
});
