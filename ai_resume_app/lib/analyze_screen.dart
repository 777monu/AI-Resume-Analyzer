import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'result_screen.dart';
class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key});

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
bool isLoading = false;
  PlatformFile? pickedFile;

  TextEditingController jobController = TextEditingController();
  TextEditingController emailController = TextEditingController();

  Future<void> pickFile() async {

    FilePickerResult? result =
        await FilePicker.platform.pickFiles();

    if (result != null) {
      setState(() {
        pickedFile = result.files.first;
      });
    }
  }
  Future<void> analyzeResume() async {

  if (pickedFile == null) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("Please choose a resume")),
    );
    return;
  }

  setState(() {
    isLoading = true;
  });

  try {

    var uri = Uri.parse("YOUR_API_URL");

    var request = http.MultipartRequest(
      'POST',
      uri,
    );

    request.files.add(
      await http.MultipartFile.fromPath(
        'resume',
        pickedFile!.path!,
      ),
    );

    request.fields['job_description'] =
        jobController.text;

    request.fields['email'] =
        emailController.text;

    var response = await request.send();

    var responseData =
        await response.stream.bytesToString();

    var decodedData = jsonDecode(responseData);

    setState(() {
      isLoading = false;
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ResultScreen(
          result: decodedData['result'],
        ),
      ),
    );

  } catch (e) {

    setState(() {
      isLoading = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("Error: $e")),
    );
  }
}

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      backgroundColor: Colors.grey[100],

      appBar: AppBar(
        title: Text("Analyze Resume"),
        centerTitle: true,
      ),

      body: Padding(
        padding: EdgeInsets.all(20),

        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              Text(
                "Upload Resume",
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),

              SizedBox(height: 25),

              // PICK FILE BUTTON
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton.icon(
                  icon: Icon(Icons.upload_file),
                  label: Text("Choose Resume"),
                  onPressed: pickFile,
                ),
              ),

              SizedBox(height: 10),

              // FILE NAME
              if (pickedFile != null)
                Text(
                  "Selected: ${pickedFile!.name}",
                  style: TextStyle(color: Colors.green),
                ),

              SizedBox(height: 25),

              // JOB DESCRIPTION
              TextField(
                controller: jobController,
                maxLines: 5,
                decoration: InputDecoration(
                  labelText: "Job Description (Optional)",
                  border: OutlineInputBorder(),
                ),
              ),

              SizedBox(height: 20),

              // EMAIL
              TextField(
                controller: emailController,
                decoration: InputDecoration(
                  labelText: "Email (Optional)",
                  border: OutlineInputBorder(),
                ),
              ),

              SizedBox(height: 30),

              // ANALYZE BUTTON
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  child: Text("Analyze Resume"),
                  onPressed: () {

                    // NEXT STEP:
                    // connect backend API here

                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}