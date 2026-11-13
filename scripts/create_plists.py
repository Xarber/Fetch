# SPDX-License-Identifier: AGPL-3.0-only
import plistlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'ios'
base={'CFBundleDevelopmentRegion':'en','CFBundleExecutable':'$(EXECUTABLE_NAME)','CFBundleIdentifier':'$(PRODUCT_BUNDLE_IDENTIFIER)','CFBundleInfoDictionaryVersion':'6.0','CFBundleName':'$(PRODUCT_NAME)','CFBundleShortVersionString':'$(MARKETING_VERSION)','CFBundleVersion':'$(CURRENT_PROJECT_VERSION)'}
app={**base,'CFBundlePackageType':'APPL','LSRequiresIPhoneOS':True,'UILaunchScreen':{},'UIApplicationSceneManifest':{'UIApplicationSupportsMultipleScenes':False},'UIFileSharingEnabled':True,'LSSupportsOpeningDocumentsInPlace':True,'NSPhotoLibraryAddUsageDescription':'Save videos you choose to your Photos library.','NSCameraUsageDescription':'Scan a one-use pairing QR code for your Fetch server.','NSLocalNetworkUsageDescription':'Connect to your self-hosted Fetch server.','NSAppTransportSecurity':{'NSAllowsLocalNetworking':True},'CFBundleURLTypes':[{'CFBundleURLName':'org.openrecode.fetch','CFBundleURLSchemes':['fetch']}],'UISupportedInterfaceOrientations':['UIInterfaceOrientationPortrait','UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'],'FetchCommit':'$(FETCH_COMMIT)','FetchServerURL':'$(FETCH_SERVER_URL)','FetchChannel':'$(FETCH_CHANNEL)'}
share={**base,'CFBundlePackageType':'XPC!','NSExtension':{'NSExtensionPointIdentifier':'com.apple.share-services','NSExtensionPrincipalClass':'$(PRODUCT_MODULE_NAME).ShareViewController','NSExtensionAttributes':{'NSExtensionActivationRule':{'NSExtensionActivationSupportsWebURLWithMaxCount':10,'NSExtensionActivationSupportsText':True}}}}
for folder,obj in [('Fetch',app),('FetchShare',share)]:
    (root/folder/'Info.plist').write_bytes(plistlib.dumps(obj))
    (root/folder/(folder+'.entitlements')).write_bytes(plistlib.dumps({'com.apple.security.application-groups':['group.org.openrecode.fetch']}))
