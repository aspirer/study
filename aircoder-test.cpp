#include <iostream>
#include <fstream>
#include <string>
#include <algorithm>

using namespace std;

int main(int argc, char* argv[]) {
    if (argc != 3) {
        cout << "Usage: remove_empty_lines <input_file> <output_file>" << endl;
        return 1;
    }

    ifstream input(argv[1]);
    if (!input.is_open()) {
        cout << "Failed to open input file: " << argv[1] << endl;
        return 1;
    }

    ofstream output(argv[2]);
    if (!output.is_open()) {
        cout << "Failed to open output file: " << argv[2] << endl;
        input.close();
        return 1;
    }

    string line;
    int count = 0;
    while (getline(input, line)) {
        // 去除空格和制表符
        line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
        // 如果该行不是空行，则写入输出文件
        if (!line.empty()) {
            output << line << endl;
            count += line.length();
        }
    }

    input.close();
    output.close();

    cout << "Number of characters written: " << count << endl;

    return 0;
}