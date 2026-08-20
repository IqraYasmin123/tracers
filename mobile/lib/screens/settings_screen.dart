import 'package:flutter/material.dart';
import '../api/client.dart';
import '../theme/theme.dart';

class SettingsScreen extends StatefulWidget {
  final ApiClient api;
  const SettingsScreen({super.key, required this.api});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _urlController;
  bool? _testResult;
  bool _testing = false;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.api.baseUrl);
  }

  Future<void> _save() async {
    await widget.api.setBaseUrl(_urlController.text.trim());
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Backend URL saved.')));
    }
  }

  Future<void> _testConnection() async {
    setState(() {
      _testing = true;
      _testResult = null;
    });
    await widget.api.setBaseUrl(_urlController.text.trim());
    final ok = await widget.api.checkHealth();
    setState(() {
      _testing = false;
      _testResult = ok;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Backend URL', style: TextStyle(color: TracerColors.muted, fontSize: 12)),
          const SizedBox(height: 6),
          TextField(controller: _urlController, keyboardType: TextInputType.url),
          const SizedBox(height: 4),
          const Text(
            'Android emulator: use 10.0.2.2 to reach your computer\'s localhost.\n'
            'Physical device: use your computer\'s LAN IP (e.g. http://192.168.1.42:8000) — '
            'both devices must be on the same Wi-Fi network.',
            style: TextStyle(color: TracerColors.muted, fontSize: 11),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ElevatedButton(onPressed: _save, child: const Text('Save')),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton(
                  onPressed: _testing ? null : _testConnection,
                  child: Text(_testing ? 'Testing…' : 'Test Connection'),
                ),
              ),
            ],
          ),
          if (_testResult != null) ...[
            const SizedBox(height: 12),
            Text(
              _testResult! ? 'Connected — backend is reachable.' : 'Could not reach the backend.',
              style: TextStyle(
                color: _testResult! ? TracerColors.verdictClean : TracerColors.verdictAdversarial,
              ),
            ),
          ],
          const SizedBox(height: 32),
          const Divider(color: TracerColors.hairline),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () async {
                await widget.api.logout();
                if (context.mounted) {
                  Navigator.of(context).pushNamedAndRemoveUntil('/', (route) => false);
                }
              },
              style: OutlinedButton.styleFrom(foregroundColor: TracerColors.verdictAdversarial),
              child: const Text('Log out'),
            ),
          ),
        ],
      ),
    );
  }
}
