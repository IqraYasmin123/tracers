import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Local-only notifications. There is no push infrastructure on the backend — no FCM
/// device-token registration, no notification records in the database (see
/// database/models.py) — so this deliberately does NOT pretend to be a push notification
/// system. It fires a notification from the same device, at the moment an action finishes
/// on that device, which is an honest and useful feature on its own (e.g. "your analysis
/// finished" while the app is backgrounded) without overstating what exists server-side.
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    const settings = InitializationSettings(android: androidSettings, iOS: iosSettings);
    await _plugin.initialize(settings);
    _initialized = true;
  }

  Future<void> showAnalysisComplete({required String verdict, required double confidence}) async {
    await init();
    const androidDetails = AndroidNotificationDetails(
      'tracer_analysis_channel',
      'Analysis Results',
      channelDescription: 'Notifies when an image analysis finishes',
      importance: Importance.high,
      priority: Priority.high,
    );
    const details = NotificationDetails(android: androidDetails, iOS: DarwinNotificationDetails());
    final confidencePct = (confidence * 100).toStringAsFixed(1);
    await _plugin.show(
      0,
      'Analysis complete',
      'Verdict: ${verdict.toUpperCase()} ($confidencePct% confidence)',
      details,
    );
  }

  Future<void> showReportReady(String format) async {
    await init();
    const androidDetails = AndroidNotificationDetails(
      'tracer_reports_channel',
      'Reports',
      channelDescription: 'Notifies when a case report finishes generating',
      importance: Importance.defaultImportance,
      priority: Priority.defaultPriority,
    );
    const details = NotificationDetails(android: androidDetails, iOS: DarwinNotificationDetails());
    await _plugin.show(1, 'Report ready', '${format.toUpperCase()} report generated successfully.', details);
  }
}
