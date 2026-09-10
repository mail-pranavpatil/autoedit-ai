require 'json'

package = JSON.parse(File.read(File.join(__dir__, 'package.json')))

Pod::Spec.new do |s|
  s.name = 'AutoeditNative'
  s.version = package['version']
  s.summary = package['description']
  s.license = { :type => 'Private' }
  s.homepage = 'https://github.com/autoedit-ai/autoedit-ai'
  s.author = 'AutoEdit AI'
  s.source = { :git => 'https://github.com/autoedit-ai/autoedit-ai.git', :tag => s.version.to_s }
  s.source_files = 'ios/Sources/**/*.swift'
  s.ios.deployment_target = '14.0'
  s.dependency 'Capacitor'
  s.swift_version = '5.1'
end
