import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;

import 'result_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: ResumeScreen(),
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

  Future<void> pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles();

    if (result != null) {
      setState(() {
        file = result.files.first;
      });
    }
  }

  Future<void> uploadResume() async {
    if (file == null) return;

    setState(() {
      loading = true;
    });

    var request = http.MultipartRequest(
      "POST",
      Uri.parse("https://YOUR-RENDER-URL.onrender.com/"),
    );

    request.files.add(
      http.MultipartFile.fromBytes(
        "resume",
        file!.bytes!,
        filename: file!.name,
      ),
    );

    request.fields["job_description"] = "Software Developer";
    request.fields["email"] = "test@gmail.com";

    var response = await request.send();
    var responseData = await response.stream.bytesToString();

    setState(() {
      loading = false;
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ResultScreen(result: responseData),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("AI Resume Analyzer")),

      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [

            SizedBox(height: 20),

            Text(
              file == null
                  ? "No file selected"
                  : "Selected: ${file!.name}",
            ),

            SizedBox(height: 20),

            ElevatedButton(
              onPressed: pickFile,
              child: Text("Pick Resume"),
            ),

            SizedBox(height: 10),

            ElevatedButton(
              onPressed: loading ? null : uploadResume,
              child: loading
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text("Analyze Resume"),
            ),
          ],
        ),
      ),
    );
  }
}