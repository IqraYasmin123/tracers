import 'package:flutter/material.dart';

/// Same color tokens as frontend/tailwind.config.js, so the mobile app looks like the
/// same product, not a reskin. Kept as plain constants (no ThemeExtension complexity)
/// since this app has a small, fixed set of screens.
class TracerColors {
  static const void_ = Color(0xFF0B0E14);
  static const panel = Color(0xFF12151D);
  static const hairline = Color(0xFF232733);
  static const ink = Color(0xFFE6E8EC);
  static const muted = Color(0xFF8B93A3);
  static const cyan = Color(0xFF3DD6C4);
  static const cyanDim = Color(0xFF2A9E92);
  static const verdictClean = Color(0xFF5FD98A);
  static const verdictAdversarial = Color(0xFFE85C4A);
  static const verdictWarning = Color(0xFFE8A83D);
}

ThemeData buildTracerTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: TracerColors.void_,
    colorScheme: base.colorScheme.copyWith(
      primary: TracerColors.cyan,
      secondary: TracerColors.cyanDim,
      surface: TracerColors.panel,
      error: TracerColors.verdictAdversarial,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: TracerColors.void_,
      foregroundColor: TracerColors.ink,
      elevation: 0,
    ),
    cardColor: TracerColors.panel,
    dividerColor: TracerColors.hairline,
    textTheme: base.textTheme.apply(
      bodyColor: TracerColors.ink,
      displayColor: TracerColors.ink,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: TracerColors.panel,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: TracerColors.hairline),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: TracerColors.hairline),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: TracerColors.cyan),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: TracerColors.cyan,
        foregroundColor: TracerColors.void_,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
  );
}

Color verdictColor(String? verdict) {
  switch (verdict) {
    case 'clean':
      return TracerColors.verdictClean;
    case 'adversarial':
      return TracerColors.verdictAdversarial;
    default:
      return TracerColors.muted;
  }
}

Color caseStatusColor(String status) {
  switch (status) {
    case 'open':
      return TracerColors.cyan;
    case 'in_progress':
      return TracerColors.verdictWarning;
    case 'closed':
      return TracerColors.verdictClean;
    case 'archived':
    default:
      return TracerColors.muted;
  }
}

String titleCaseStatus(String status) =>
    status.split('_').map((w) => w.isEmpty ? w : w[0].toUpperCase() + w.substring(1)).join(' ');
