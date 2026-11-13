# SPDX-License-Identifier: AGPL-3.0-only
require 'xcodeproj'
root = File.expand_path('../ios', __dir__)
project = Xcodeproj::Project.new(File.join(root, 'Fetch.xcodeproj'))
app = project.new_target(:application, 'Fetch', :ios, '17.0')
share = project.new_target(:app_extension, 'FetchShare', :ios, '17.0')
[[app, ['Fetch', 'FetchCore']], [share, ['FetchShare']]].each do |target, folders|
  folders.each do |folder|
    group = project.main_group.new_group(folder, folder)
    Dir.glob(File.join(root, folder, '*.swift')).sort.each do |path|
      ref = group.new_file(File.basename(path)); target.source_build_phase.add_file_reference(ref)
    end
  end
  target.build_configurations.each do |config|
    config.build_settings.merge!({
      'FETCH_CHANNEL'=>'stable', 'FETCH_COMMIT'=>'development', 'SWIFT_VERSION'=>'6.0', 'SWIFT_STRICT_CONCURRENCY'=>'complete',
      'SWIFT_APPROACHABLE_CONCURRENCY'=>'YES',
      'PRODUCT_BUNDLE_IDENTIFIER'=> target == app ? 'org.openrecode.fetch' : 'org.openrecode.fetch.share',
      'INFOPLIST_FILE'=> target == app ? 'Fetch/Info.plist' : 'FetchShare/Info.plist',
      'CODE_SIGN_ENTITLEMENTS'=> target == app ? 'Fetch/Fetch.entitlements' : 'FetchShare/FetchShare.entitlements',
      'CODE_SIGN_STYLE'=>'Automatic', 'CURRENT_PROJECT_VERSION'=>'1', 'MARKETING_VERSION'=>'0.1.0',
      'TARGETED_DEVICE_FAMILY'=>'1,2', 'GENERATE_INFOPLIST_FILE'=>'NO'
    })
    config.build_settings['APPLICATION_EXTENSION_API_ONLY']='YES' if target == share
    config.build_settings['SKIP_INSTALL']='YES' if target == share
  end
end
['Fetch/Assets.xcassets','Fetch/ReleaseMetadata.json','Fetch/PrivacyInfo.xcprivacy'].each do |path|
  resources = project.main_group.new_file(path)
  app.resources_build_phase.add_file_reference(resources)
end
app.build_configurations.each { |config| config.build_settings['ASSETCATALOG_COMPILER_APPICON_NAME']='AppIcon' }
share.resources_build_phase.add_file_reference(project.main_group.new_file('FetchShare/PrivacyInfo.xcprivacy'))
app.add_dependency(share)
phase=app.new_copy_files_build_phase('Embed Extensions'); phase.dst_subfolder_spec='13'
phase.add_file_reference(share.product_reference)
project.save
scheme=Xcodeproj::XCScheme.new
scheme.add_build_target(app)
scheme.set_launch_target(app)
scheme.save_as(project.path, 'Fetch', true)
puts project.path
