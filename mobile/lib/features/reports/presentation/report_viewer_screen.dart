import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/api/api_client.dart';
import '../../../app/theme/app_theme.dart';

class ReportViewerScreen extends ConsumerStatefulWidget {
  final int reportId;
  
  const ReportViewerScreen({super.key, required this.reportId});

  @override
  ConsumerState<ReportViewerScreen> createState() => _ReportViewerScreenState();
}

class _ReportViewerScreenState extends ConsumerState<ReportViewerScreen> {
  Map<String, dynamic>? _report;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadReport();
  }

  Future<void> _loadReport() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = ApiClient();
      final reports = await apiClient.getReports();
      _report = reports.firstWhere(
        (r) => r['id'] == widget.reportId,
        orElse: () => null,
      );
      setState(() => _isLoading = false);
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _downloadPDF() async {
    try {
      final apiClient = ApiClient();
      final url = await apiClient.getReportDownloadUrl(widget.reportId);
      
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error descargando PDF: $e'),
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
        appBar: AppBar(title: const Text('Reporte')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_report == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Reporte')),
        body: const Center(child: Text('Reporte no encontrado')),
      );
    }

    final score = _report!['overall_vulnerability_score']?.toDouble() ?? 0.0;
    final recommendations = List<String>.from(_report!['recommendations'] ?? []);

    return Scaffold(
      appBar: AppBar(
        title: Text(_report!['title'] ?? 'Reporte'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            onPressed: _downloadPDF,
            tooltip: 'Descargar PDF',
          ),
          if (_report!['model_viewer_url'] != null)
            IconButton(
              icon: const Icon(Icons.view_in_ar),
              onPressed: () {
                // Open 3D viewer
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Visor 3D - Próximamente')),
                );
              },
              tooltip: 'Ver modelo 3D',
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Vulnerability score card
            Card(
              color: _getVulnerabilityColor(score).withOpacity(0.1),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Text(
                      'Score de Vulnerabilidad',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey[700],
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: 120,
                      height: 120,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: score / 100,
                            strokeWidth: 12,
                            backgroundColor: Colors.grey[200],
                            color: _getVulnerabilityColor(score),
                          ),
                          Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                '${score.toInt()}',
                                style: TextStyle(
                                  fontSize: 32,
                                  fontWeight: FontWeight.bold,
                                  color: _getVulnerabilityColor(score),
                                ),
                              ),
                              Text(
                                '/100',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: _getVulnerabilityColor(score),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        _getVulnerabilityLabel(score),
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Summary
            if (_report!['summary'] != null) ...[
              Text(
                'Resumen',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_report!['summary']),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // Score breakdown
            Text(
              'Desglose de Scores',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _buildScoreRow('Estructural', _report!['structural_score']?.toDouble()),
                    const Divider(),
                    _buildScoreRow('Confinamiento', _report!['confinement_score']?.toDouble()),
                    const Divider(),
                    _buildScoreRow('Conexiones', _report!['connection_score']?.toDouble()),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Recommendations
            if (recommendations.isNotEmpty) ...[
              Text(
                'Recomendaciones',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: recommendations.asMap().entries.map((entry) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryColor,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Center(
                                child: Text(
                                  '${entry.key + 1}',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(entry.value),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildScoreRow(String label, double? score) {
    final value = score ?? 0.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Text(label),
          ),
          SizedBox(
            width: 120,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: value / 100,
                backgroundColor: Colors.grey[200],
                color: _getVulnerabilityColor(value),
                minHeight: 8,
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 40,
            child: Text(
              '${value.toInt()}%',
              textAlign: TextAlign.right,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: _getVulnerabilityColor(value),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getVulnerabilityColor(double score) {
    if (score < 25) return AppTheme.vulnLow;
    if (score < 50) return AppTheme.vulnMedium;
    if (score < 75) return AppTheme.vulnHigh;
    return AppTheme.vulnCritical;
  }

  String _getVulnerabilityLabel(double score) {
    if (score < 25) return 'BAJO';
    if (score < 50) return 'MEDIO';
    if (score < 75) return 'ALTO';
    return 'CRÍTICO';
  }
}
