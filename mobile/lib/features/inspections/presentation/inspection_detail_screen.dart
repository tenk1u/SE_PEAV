import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../app/theme/app_theme.dart';

class InspectionDetailScreen extends ConsumerStatefulWidget {
  final int inspectionId;
  
  const InspectionDetailScreen({super.key, required this.inspectionId});

  @override
  ConsumerState<InspectionDetailScreen> createState() => _InspectionDetailScreenState();
}

class _InspectionDetailScreenState extends ConsumerState<InspectionDetailScreen> {
  Map<String, dynamic>? _inspection;
  Map<String, dynamic>? _status;
  List<dynamic> _detections = [];
  List<dynamic> _metrics = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = ApiClient();
      
      // Load inspection details
      final inspections = await apiClient.getInspections();
      _inspection = inspections.firstWhere(
        (i) => i['id'] == widget.inspectionId,
        orElse: () => null,
      );
      
      // Load status
      _status = await apiClient.getInspectionStatus(widget.inspectionId);
      
      // Load detections and metrics if completed
      if (_status?['status'] == 'completed') {
        _detections = await apiClient.getDetections(widget.inspectionId);
        _metrics = await apiClient.getMetrics(widget.inspectionId);
      }
      
      setState(() => _isLoading = false);
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _triggerProcessing() async {
    try {
      final apiClient = ApiClient();
      await apiClient.triggerProcessing(widget.inspectionId);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Procesamiento iniciado'),
            backgroundColor: AppTheme.successColor,
          ),
        );
        _loadData(); // Refresh
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Inspección')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Inspección #${widget.inspectionId}'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: _getStatusColor(_status?['status']).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            _getStatusIcon(_status?['status']),
                            color: _getStatusColor(_status?['status']),
                            size: 32,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _getStatusLabel(_status?['status']),
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: _getStatusColor(_status?['status']),
                                ),
                              ),
                              if (_status?['current_step'] != null)
                                Text(
                                  _status!['current_step'],
                                  style: TextStyle(color: Colors.grey[600]),
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    if (_status?['status'] == 'processing') ...[
                      const SizedBox(height: 16),
                      LinearProgressIndicator(
                        value: (_status?['progress_percentage'] ?? 0) / 100,
                        backgroundColor: Colors.grey[200],
                        minHeight: 8,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${_status?['progress_percentage'] ?? 0}% completado',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Actions
            if (_status?['status'] == 'pending')
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _triggerProcessing,
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('Iniciar Procesamiento'),
                ),
              ),
            
            if (_status?['status'] == 'completed') ...[
              // Detections summary
              Text(
                'Elementos Detectados',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              if (_detections.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No se detectaron elementos'),
                  ),
                )
              else
                _buildDetectionsSummary(),
              const SizedBox(height: 24),

              // Metrics
              Text(
                'Análisis E.060',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              if (_metrics.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No hay métricas disponibles'),
                  ),
                )
              else
                ...List.generate(_metrics.length, (index) {
                  return _MetricCard(metric: _metrics[index]);
                }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetectionsSummary() {
    final Map<String, int> classCounts = {};
    for (final det in _detections) {
      final className = det['class_name'] ?? 'unknown';
      classCounts[className] = (classCounts[className] ?? 0) + 1;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: classCounts.entries.map((entry) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(entry.key, style: const TextStyle(fontWeight: FontWeight.w500)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${entry.value}',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryColor,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'completed': return AppTheme.successColor;
      case 'processing': return AppTheme.warningColor;
      case 'failed': return AppTheme.errorColor;
      default: return Colors.grey;
    }
  }

  IconData _getStatusIcon(String? status) {
    switch (status) {
      case 'completed': return Icons.check_circle;
      case 'processing': return Icons.sync;
      case 'failed': return Icons.error;
      default: return Icons.hourglass_empty;
    }
  }

  String _getStatusLabel(String? status) {
    switch (status) {
      case 'completed': return 'Completado';
      case 'processing': return 'Procesando';
      case 'failed': return 'Error';
      case 'pending': return 'Pendiente';
      default: return status ?? 'Desconocido';
    }
  }
}

class _MetricCard extends StatelessWidget {
  final Map<String, dynamic> metric;

  const _MetricCard({required this.metric});

  @override
  Widget build(BuildContext context) {
    final vulnLevel = metric['vulnerability_level'] ?? 'low';
    final vulnScore = metric['vulnerability_score'] ?? 0;
    final issues = List<String>.from(metric['issues_found'] ?? []);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${metric['element_type']} #${metric['element_id']}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.getVulnerabilityColor(vulnLevel).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    AppTheme.getVulnerabilityLabel(vulnLevel),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.getVulnerabilityColor(vulnLevel),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Compliance indicators
            Row(
              children: [
                _buildComplianceChip('Espesor', metric['meets_minimum_thickness']),
                const SizedBox(width: 8),
                _buildComplianceChip('Confinamiento', metric['meets_confinement']),
                const SizedBox(width: 8),
                _buildComplianceChip('Vano/Muro', metric['meets_vo_ratio']),
              ],
            ),
            if (issues.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...issues.map((issue) => Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Row(
                  children: [
                    const Icon(Icons.warning, size: 14, color: AppTheme.warningColor),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        issue,
                        style: TextStyle(fontSize: 12, color: Colors.grey[700]),
                      ),
                    ),
                  ],
                ),
              )),
            ],
            const SizedBox(height: 8),
            // Vulnerability score bar
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Vulnerabilidad: $vulnScore/100',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: vulnScore / 100,
                  backgroundColor: Colors.grey[200],
                  color: AppTheme.getVulnerabilityColor(vulnLevel),
                  minHeight: 6,
                  borderRadius: BorderRadius.circular(3),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildComplianceChip(String label, String? value) {
    final isCompliant = value == 'yes';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isCompliant ? AppTheme.successColor.withOpacity(0.1) : AppTheme.errorColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isCompliant ? Icons.check : Icons.close,
            size: 14,
            color: isCompliant ? AppTheme.successColor : AppTheme.errorColor,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: isCompliant ? AppTheme.successColor : AppTheme.errorColor,
            ),
          ),
        ],
      ),
    );
  }
}
