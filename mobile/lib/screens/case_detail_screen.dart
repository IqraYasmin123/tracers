import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../api/client.dart';
import '../models/models.dart';
import '../notifications/notification_service.dart';
import '../theme/theme.dart';
import '../widgets/case_status_badge.dart';
import '../widgets/verdict_badge.dart';

const _statusOptions = ['open', 'in_progress', 'closed', 'archived'];

class CaseDetailScreen extends StatefulWidget {
  final ApiClient api;
  final String caseId;
  const CaseDetailScreen({super.key, required this.api, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> {
  late Future<CaseDetail> _caseFuture;
  late Future<List<ReportSummary>> _reportsFuture;
  bool _updatingStatus = false;
  String? _generatingFormat;
  String? _generateError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _caseFuture = widget.api.getCase(widget.caseId);
    _reportsFuture = widget.api.listReports(widget.caseId);
  }

  Future<void> _updateStatus(String status) async {
    setState(() => _updatingStatus = true);
    try {
      await widget.api.updateCaseStatus(widget.caseId, status);
      setState(_load);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not update status: $e')));
      }
    } finally {
      if (mounted) setState(() => _updatingStatus = false);
    }
  }

  Future<void> _generateReport(String format) async {
    setState(() {
      _generatingFormat = format;
      _generateError = null;
    });
    try {
      await widget.api.generateReport(widget.caseId, format: format);
      await NotificationService().showReportReady(format);
      setState(_load);
    } catch (e) {
      setState(() => _generateError = e.toString());
    } finally {
      if (mounted) setState(() => _generatingFormat = null);
    }
  }

  Future<void> _downloadReport(ReportSummary report) async {
    final url = widget.api.reportDownloadUrl(widget.caseId, report.id);
    final uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Could not open the report download link.')));
      }
    }
  }

  String _formatBytes(int bytes) {
    if (bytes <= 0) return '—';
    if (bytes < 1024) return '$bytes B';
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Case Detail')),
      body: FutureBuilder<CaseDetail>(
        future: _caseFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Text('Could not load this case: ${snapshot.error}',
                  style: const TextStyle(color: TracerColors.verdictAdversarial)),
            );
          }
          final caseData = snapshot.data!;
          return RefreshIndicator(
            onRefresh: () async => setState(_load),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: TracerColors.panel,
                    border: Border.all(color: TracerColors.hairline),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(caseData.caseNumber,
                          style: const TextStyle(color: TracerColors.muted, fontSize: 12)),
                      const SizedBox(height: 4),
                      Text(caseData.title,
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      if (caseData.description != null) ...[
                        const SizedBox(height: 4),
                        Text(caseData.description!, style: const TextStyle(color: TracerColors.muted)),
                      ],
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          CaseStatusBadge(status: caseData.status),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButton<String>(
                              value: caseData.status,
                              isExpanded: true,
                              underline: const SizedBox(),
                              items: [
                                for (final s in _statusOptions)
                                  DropdownMenuItem(value: s, child: Text(s.replaceAll('_', ' ')))
                              ],
                              onChanged: _updatingStatus ? null : (v) => v == null ? null : _updateStatus(v),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Text('Evidence (${caseData.evidenceCount})',
                    style: const TextStyle(color: TracerColors.muted, fontSize: 12, letterSpacing: 0.6)),
                const SizedBox(height: 8),
                if (caseData.evidence.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(
                      child: Text('No evidence attached to this case yet.',
                          style: TextStyle(color: TracerColors.muted)),
                    ),
                  )
                else
                  for (final ev in caseData.evidence) _EvidenceCard(evidence: ev),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Reports',
                        style: TextStyle(color: TracerColors.muted, fontSize: 12, letterSpacing: 0.6)),
                    Row(
                      children: [
                        TextButton(
                          onPressed: _generatingFormat != null ? null : () => _generateReport('pdf'),
                          child: Text(_generatingFormat == 'pdf' ? 'Generating…' : '+ PDF'),
                        ),
                        TextButton(
                          onPressed: _generatingFormat != null ? null : () => _generateReport('docx'),
                          child: Text(_generatingFormat == 'docx' ? 'Generating…' : '+ DOCX'),
                        ),
                      ],
                    ),
                  ],
                ),
                if (_generateError != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(_generateError!, style: const TextStyle(color: TracerColors.verdictAdversarial)),
                  ),
                FutureBuilder<List<ReportSummary>>(
                  future: _reportsFuture,
                  builder: (context, reportSnapshot) {
                    if (!reportSnapshot.hasData) {
                      return const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12),
                        child: Text('Loading reports…', style: TextStyle(color: TracerColors.muted)),
                      );
                    }
                    final reports = reportSnapshot.data!;
                    if (reports.isEmpty) {
                      return const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12),
                        child: Text('No reports generated yet.', style: TextStyle(color: TracerColors.muted)),
                      );
                    }
                    return Column(
                      children: [
                        for (final r in reports)
                          Container(
                            margin: const EdgeInsets.only(top: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            decoration: BoxDecoration(
                              color: TracerColors.panel,
                              border: Border.all(color: TracerColors.hairline),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text('${r.format.toUpperCase()} · ${_formatBytes(r.fileSizeBytes)}',
                                    style: const TextStyle(fontSize: 13)),
                                TextButton(
                                  onPressed: () => _downloadReport(r),
                                  child: const Text('Download →'),
                                ),
                              ],
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _EvidenceCard extends StatelessWidget {
  final EvidenceSummary evidence;
  const _EvidenceCard({required this.evidence});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: TracerColors.panel,
        border: Border.all(color: TracerColors.hairline),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(evidence.originalFilename, style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(
            '${evidence.sha256Hash.substring(0, 12)}… · ${evidence.uploadedAt.toLocal()}'.split('.').first,
            style: const TextStyle(color: TracerColors.muted, fontSize: 11),
          ),
          if (evidence.aiResult != null) ...[
            const SizedBox(height: 8),
            VerdictBadge(
              verdict: evidence.aiResult!.verdict,
              confidence: evidence.aiResult!.confidence,
            ),
          ],
        ],
      ),
    );
  }
}
