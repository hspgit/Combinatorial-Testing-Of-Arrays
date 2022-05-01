#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <unordered_set>
#include <set>
using namespace std;

double DegreeOfSaturation(vector<int> &levels, int rows){
    double dos = 0;
    // pair wise addition of (#levels-1) of all the parameters/symbols.
    for(int i = 0; i < levels.size(); i++){
        dos += (levels[i] - 1);
    }
    // dividing by (no. of tests-1)
    dos = dos/(rows - 1);
    return dos;
}



int main()
{
    // taking filename as input from user
    string filename;
    cout << "Please enter the name of the input file." << endl;
    cin >> filename;
    
    int rows = 0, columns = 0;
    ifstream iFile;
    iFile.open(filename);
    // If there is a error in opening file
    if (!iFile)
    {
        cerr << "Error in opening file" << endl;
        return 1;
    }
    // Taking rows as input from the file
    iFile >> rows;
    // Taking columns as input from the file
    iFile >> columns;
    // Initializing levels
    vector<int> levels(columns, 0);
    for (int i = 0; i < columns; i++)
    {
        iFile >> levels[i];
    }
    // Initializing zeros
    vector<int> zeros(columns + 1, 0);
    for (int i = 0; i < columns + 1; i++)
    {
        iFile >> zeros[i];
    }
    // Initializing a matrix having given rows and columns
    vector<vector<int>> vec;

    for (int i = 0; i < rows; i++)
    {
        vec.push_back({});
    }
    // Taking elements of matrix as an input from the file
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < columns; j++)
        {
            int temp;
            iFile >> temp;
            vec[i].push_back(temp);
        }
    }
    // Closing the input file
    iFile.close();
    // passing the levels-array and number of rows to find degree of saturation
    double dos = DegreeOfSaturation(levels, rows);
    // cout << dos;
    cout << "Degree Of Saturation = " << dos << endl;
    if(dos > 1){
        cout << "The Degree Of Saturation of Design is greater than 1, ";
        cout << "hence the design is SUPER-SATURATED" << endl;
    }
    else if(dos <= 1){
        cout << "The Degree Of Saturation of Design is NOT greater than 1, ";
        cout << "hence the design is NOT super-satuturated" << endl;
    }
    return 0;
}

