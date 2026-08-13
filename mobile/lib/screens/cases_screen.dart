import 'package:flutter/material.dart';
import '../api/client.dart';
import '../models/models.dart';
import '../theme/theme.dart';
import '../widgets/case_status_badge.dart';
import 'case_detail_screen.dart';

const _statusFilters = [
  {'value': null, 'label': 'All'},
  {'value': 'open', 'label': 'Open'},
  {'value': 'in_progress', 'label': 'In Progress'},
  {'value': 'closed', 'label': 'Closed'},
  {'value': 'archived', 'label': 'Archived'},
];

class CasesScreen extends StatefulWidget {
  final ApiClient api;
  const CasesScreen({super.key, required this.api});

  @override
  State<CasesScreen> createState() => _CasesScreenState();
}

class _CasesScreenState extends State<CasesScreen> {
  String? _statusFilter;
  late Future<List<CaseSummary>> _casesFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _casesFuture = widget.api.listCases(status: _statusFilter);
  }

  Future<void> _showCreateCaseDialog() async {
    final titleController = TextEditingController();
    final descController = TextEditingController();
    String? error;

    await showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: TracerColors.panel,
          title: const Text('New Case'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: titleController, decoration: const InputDecoration(labelText: 'Title')),
              const SizedBox(height: 12),
              TextField(
                controller: descController,
                decoration: const InputDecoration(labelText: 'Description (optional)'),
              ),
              if (error != null) ...[
                const SizedBox(height: 8),
                Text(error!, style: const TextStyle(color: TracerColors.verdictAdversarial)),
              ],
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                if (titleController.text.trim().isEmpty) {
                  setDialogState(() => error = 'Title is required.');
                  return;
                }
                try {
                  await widget.api.createCase(
                    title: titleController.text.trim(),
                    description: descController.text.trim().isEmpty ? null : descController.text.trim(),
                  );
                  if (context.mounted) Navigator.of(context).pop();
                  setState(_load);
                } catch (e) {
                  setDialogState(() => error = e.toString());
                }
              },
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cases')),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateCaseDialog,
        backgroundColor: TracerColors.cyan,
        foregroundColor: TracerColors.void_,
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              children: [
                for (final f in _statusFilters)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(f['label'] as String),
                      selected: _statusFilter == f['value'],
                      onSelected: (_) => setState(() {
                        _statusFilter = f['value'] as String?;
                        _load();
                      }),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<List<CaseSummary>>(
              future: _casesFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(
                    child: Text('Could not load cases: ${snapshot.error}',
                        style: const TextStyle(color: TracerColors.verdictAdversarial)),
                  );
                }
                final cases = snapshot.data!;
                if (cases.isEmpty) {
                  return const Center(
                    child: Text('No cases yet.', style: TextStyle(color: TracerColors.muted)),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => setState(_load),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: cases.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, i) {
                      final c = cases[i];
                      return Container(
                        decoration: BoxDecoration(
                          color: TracerColors.panel,
                          border: Border.all(color: TracerColors.hairline),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: ListTile(
                          title: Text(c.title),
                          subtitle: Text('${c.caseNumber} · ${c.evidenceCount} evidence',
                              style: const TextStyle(color: TracerColors.muted, fontSize: 12)),
                          trailing: CaseStatusBadge(status: c.status),
                          onTap: () async {
                            await Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (context) => CaseDetailScreen(api: widget.api, caseId: c.id),
                              ),
                            );
                            setState(_load);
                          },
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
