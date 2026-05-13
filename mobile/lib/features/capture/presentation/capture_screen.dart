import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../core/api/api_client.dart';
import '../../../app/theme/app_theme.dart';

class CaptureScreen extends ConsumerStatefulWidget {
  const CaptureScreen({super.key});

  @override
  ConsumerState<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends ConsumerState<CaptureScreen> {
  CameraController? _cameraController;
  List<CameraDescription> _cameras = [];
  bool _isInitialized = false;
  bool _isRecording = false;
  bool _hasLiDAR = false; // Detectar si tiene LiDAR
  
  List<dynamic> _inspections = [];
  int? _selectedInspectionId;
  bool _isLoadingInspections = true;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _loadInspections();
    _checkLiDAR();
  }

  Future<void> _checkLiDAR() async {
    // En una implementación real, verificaríamos si el dispositivo tiene LiDAR
    // Por ahora, asumimos que no
    setState(() => _hasLiDAR = false);
  }

  Future<void> _initializeCamera() async {
    final status = await Permission.camera.request();
    if (status.isGranted) {
      _cameras = await availableCameras();
      if (_cameras.isNotEmpty) {
        _cameraController = CameraController(
          _cameras[0],
          ResolutionPreset.high,
          enableAudio: true,
        );
        await _cameraController!.initialize();
        setState(() => _isInitialized = true);
      }
    }
  }

  Future<void> _loadInspections() async {
    setState(() => _isLoadingInspections = true);
    try {
      final apiClient = ApiClient();
      final inspections = await apiClient.getInspections();
      setState(() {
        _inspections = inspections.where((i) => i['status'] == 'pending').toList();
        _isLoadingInspections = false;
      });
    } catch (e) {
      setState(() => _isLoadingInspections = false);
    }
  }

  Future<void> _startStopRecording() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) return;

    if (_isRecording) {
      final file = await _cameraController!.stopVideoRecording();
      setState(() => _isRecording = false);
      
      if (_selectedInspectionId != null) {
        _uploadVideo(file.path);
      }
    } else {
      await _cameraController!.startVideoRecording();
      setState(() => _isRecording = true);
    }
  }

  Future<void> _takePicture() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) return;

    final file = await _cameraController!.takePicture();
    
    if (_selectedInspectionId != null) {
      _uploadImage(file.path);
    }
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final files = await picker.pickMultipleMedia();
    
    if (files.isNotEmpty && _selectedInspectionId != null) {
      _uploadImages(files.map((f) => f.path).toList());
    }
  }

  Future<void> _uploadVideo(String path) async {
    if (_selectedInspectionId == null) {
      _showSelectInspectionWarning();
      return;
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Subiendo video...'),
          ],
        ),
      ),
    );

    try {
      final apiClient = ApiClient();
      await apiClient.uploadVideo(
        inspectionId: _selectedInspectionId!,
        filePath: path,
        fileName: 'video_${DateTime.now().millisecondsSinceEpoch}.mp4',
      );
      
      if (mounted) {
        Navigator.pop(context); // Close loading
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Video subido exitosamente'),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context); // Close loading
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error subiendo video: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  Future<void> _uploadImage(String path) async {
    if (_selectedInspectionId == null) {
      _showSelectInspectionWarning();
      return;
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Subiendo imagen...'),
          ],
        ),
      ),
    );

    try {
      final apiClient = ApiClient();
      await apiClient.uploadImages(
        inspectionId: _selectedInspectionId!,
        filePaths: [path],
      );
      
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Imagen subida exitosamente'),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error subiendo imagen: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  Future<void> _uploadImages(List<String> paths) async {
    if (_selectedInspectionId == null) {
      _showSelectInspectionWarning();
      return;
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Subiendo imágenes...'),
          ],
        ),
      ),
    );

    try {
      final apiClient = ApiClient();
      await apiClient.uploadImages(
        inspectionId: _selectedInspectionId!,
        filePaths: paths,
      );
      
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${paths.length} imágenes subidas exitosamente'),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error subiendo imágenes: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  void _showSelectInspectionWarning() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Selecciona una inspección primero'),
        backgroundColor: AppTheme.warningColor,
      ),
    );
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Capturar'),
        actions: [
          if (_hasLiDAR)
            IconButton(
              icon: const Icon(Icons.view_in_ar),
              tooltip: 'Escanear con LiDAR',
              onPressed: () {
                // Navigate to LiDAR scanner
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('LiDAR Scanner - Próximamente')),
                );
              },
            ),
        ],
      ),
      body: Column(
        children: [
          // Inspection selector
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey[100],
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Inspección activa:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                if (_isLoadingInspections)
                  const LinearProgressIndicator()
                else if (_inspections.isEmpty)
                  const Text(
                    'No hay inspecciones pendientes. Crea una en Proyectos.',
                    style: TextStyle(color: Colors.grey),
                  )
                else
                  DropdownButtonFormField<int>(
                    value: _selectedInspectionId,
                    decoration: const InputDecoration(
                      contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      border: OutlineInputBorder(),
                    ),
                    hint: const Text('Seleccionar inspección'),
                    items: _inspections.map((inspection) {
                      return DropdownMenuItem<int>(
                        value: inspection['id'],
                        child: Text('Inspección #${inspection['id']} - ${inspection['capture_source']}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() => _selectedInspectionId = value);
                    },
                  ),
              ],
            ),
          ),

          // Camera preview
          Expanded(
            child: _isInitialized
                ? Stack(
                    alignment: Alignment.center,
                    children: [
                      CameraPreview(_cameraController!),
                      if (_isRecording)
                        Positioned(
                          top: 16,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.red,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.fiber_manual_record, color: Colors.white, size: 16),
                                SizedBox(width: 4),
                                Text(
                                  'GRABANDO',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  )
                : const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Inicializando cámara...'),
                      ],
                    ),
                  ),
          ),

          // Controls
          Container(
            padding: const EdgeInsets.symmetric(vertical: 24),
            color: Colors.black87,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Gallery button
                IconButton(
                  onPressed: _pickFromGallery,
                  icon: const Icon(Icons.photo_library, color: Colors.white, size: 32),
                  tooltip: 'Galería',
                ),
                
                // Record button
                GestureDetector(
                  onTap: _takePicture,
                  onLongPress: _startStopRecording,
                  child: Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 4),
                      color: _isRecording ? Colors.red : Colors.transparent,
                    ),
                    child: Icon(
                      _isRecording ? Icons.stop : Icons.camera,
                      color: Colors.white,
                      size: 36,
                    ),
                  ),
                ),
                
                // Switch camera button
                IconButton(
                  onPressed: () async {
                    if (_cameras.length > 1) {
                      final currentIdx = _cameras.indexOf(_cameraController!.description);
                      final newIdx = (currentIdx + 1) % _cameras.length;
                      await _cameraController!.dispose();
                      _cameraController = CameraController(
                        _cameras[newIdx],
                        ResolutionPreset.high,
                      );
                      await _cameraController!.initialize();
                      setState(() {});
                    }
                  },
                  icon: const Icon(Icons.flip_camera_ios, color: Colors.white, size: 32),
                  tooltip: 'Cambiar cámara',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
