import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'login_screen.dart';
import 'result_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: DashboardScreen(),
    );
  }
}

class ResumeScreen extends StatefulWidget {
  @override
  _ResumeScreenState createState() => _ResumeScreenState();
}

class _ResumeScreenState extends State<ResumeScreen> {
  PlatformFile? file;
  bool loading = false;

  // 📁 PICK FILE
  Future<void> pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx'],
      withData: true,
    );

    if (result != null) {
      setState(() {
        file = result.files.first;
      });
    }
  }

  // 🚀 UPLOAD RESUME
  Future<void> uploadResume() async {
    if (file == null) return;

    setState(() {
      loading = true;
    });

    try {
      var request = http.MultipartRequest(
        "POST",
        Uri.parse("https://ai-resume-analyzer-1-piwh.onrender.com"),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          "resume",
          file!.bytes!,
          filename: file!.name,
        ),
      );

      var response = await request.send().timeout(
        Duration(seconds: 20),
        onTimeout: () {
          throw Exception("Server timeout");
        },
      );

      var responseData = await response.stream.bytesToString();

      setState(() {
        loading = false;
      });
Navigator.pushAndRemoveUntil(
  context,
  MaterialPageRoute(builder: (context) => DashboardScreen()),
  (route) => false,
);
  
    } catch (e) {
      setState(() {
        loading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("AI Resume Analyzer"),
        centerTitle: true,
      ),

      body: loading
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 20),
                  Text("Analyzing Resume..."),
                ],
              ),
            )
          : Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [

                  SizedBox(height: 20),

                  Text(
                    "AI Resume Analyzer",
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),

                  SizedBox(height: 30),

                  Container(
                    padding: EdgeInsets.all(15),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      file == null
                          ? "No file selected"
                          : "Selected File: ${file!.name}",
                      style: TextStyle(fontSize: 14),
                    ),
                  ),

                  SizedBox(height: 20),

                  ElevatedButton.icon(
                    onPressed: pickFile,
                    icon: Icon(Icons.upload_file),
                    label: Text("Pick Resume"),
                  ),

                  SizedBox(height: 10),

                  ElevatedButton.icon(
                    onPressed: loading ? null : uploadResume,
                    icon: Icon(Icons.analytics),
                    label: Text("Analyze Resume"),
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.all(15),
                    ),
                  ),

                  SizedBox(height: 20),

                  Text(
                    "Upload PDF or DOCX resume to analyze ATS score",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
    );
  }
}