import 'package:flutter/material.dart';
import '../api/client.dart';
import '../models/models.dart';
import '../theme/theme.dart';

class DashboardScreen extends StatefulWidget {
  final ApiClient api;
  const DashboardScreen({super.key, required this.api});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<CaseStats> _statsFuture;
  late Future<bool> _healthFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _statsFuture = widget.api.getCaseStats();
    _healthFuture = widget.api.checkHealth();
  }

  Future<void> _refresh() async {
    setState(_load);
    try {
      await _statsFuture;
    } catch (_) {
      // surfaced by the FutureBuilder's error branch below; nothing more to do here
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          FutureBuilder<bool>(
            future: _healthFuture,
            builder: (context, snapshot) {
              final online = snapshot.data ?? false;
              return Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Row(
                  children: [
                    Icon(Icons.circle, size: 10, color: online ? TracerColors.verdictClean : TracerColors.verdictAdversarial),
                    const SizedBox(width: 6),
                    Text(online ? 'AI engine online' : 'Backend unreachable',
                        style: const TextStyle(fontSize: 12, color: TracerColors.muted)),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<CaseStats>(
          future: _statsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  Text('Could not load stats: ${snapshot.error}',
                      style: const TextStyle(color: TracerColors.verdictAdversarial)),
                  const SizedBox(height: 8),
                  const Text(
                    'Check the backend URL in Settings and that uvicorn is running.',
                    style: TextStyle(color: TracerColors.muted),
                  ),
                ],
              );
            }
            final stats = snapshot.data!;
            return GridView.count(
              padding: const EdgeInsets.all(16),
              crossAxisCount: 2,
              childAspectRatio: 1.6,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              children: [
                _StatCard(label: 'Total Cases', value: '${stats.totalCases}'),
                _StatCard(label: 'Total Evidence', value: '${stats.totalEvidence}'),
                _StatCard(
                  label: 'Clean Images',
                  value: '${stats.cleanVerdicts}',
                  color: TracerColors.verdictClean,
                ),
                _StatCard(
                  label: 'Attacks Detected',
                  value: '${stats.adversarialVerdicts}',
                  color: TracerColors.verdictAdversarial,
                ),
                _StatCard(label: 'Open Cases', value: '${stats.openCases}'),
                _StatCard(
                  label: 'Avg. Confidence',
                  value: stats.avgConfidence == null
                      ? '—'
                      : '${(stats.avgConfidence! * 100).toStringAsFixed(1)}%',
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;
  const _StatCard({required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: TracerColors.panel,
        border: Border.all(color: TracerColors.hairline),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(value,
              style: TextStyle(
                  fontSize: 26, fontWeight: FontWeight.bold, color: color ?? TracerColors.ink)),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12, color: TracerColors.muted)),
        ],
      ),
    );
  }
}
