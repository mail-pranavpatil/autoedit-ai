import 'package:flutter/material.dart';

/// App-wide theme mode, read by [MaterialApp] and written by the Settings
/// "Appearance" control. Plain [ValueNotifier] — no state-mgmt package needed
/// for a single value read in one place.
final ValueNotifier<ThemeMode> themeModeNotifier = ValueNotifier(ThemeMode.system);
