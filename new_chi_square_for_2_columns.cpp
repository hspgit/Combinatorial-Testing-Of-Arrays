#include <bits/stdc++.h>
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

vector<double> final;
map<double, int> summaryTable;
void chi_square(vector<vector<int>> &vec, vector<int> &levels, vector<vector<double>> &chi_square_array)
{
    int rows = vec.size();
    // Finding total number of columns in our array
    int cols = vec[0].size();

    // Running a loop to select first symbol of our pair(since t = 2)
    //  We are looking at all possible pairs (i, j) such that 0 <= i < j
    for (int i = 0; i < cols - 1; i++)
    {
        // After fixing first symbol, we select a every possible symbol there is after i
        for (int j = i + 1; j < cols; j++)
        {

            // Making an unordered map for find frequency of all symbol pair present in the matrix
            unordered_map<string, double> mp;
            // Checking for all rows for particular symbol pairs(i, j) and increasing their frequency by 1
            for (int k = 0; k < rows; k++)
            {
                // Making a string of the form "(i,j)" and inserting and increasing value by one
                string s = "";
                s += to_string(vec[k][i]);
                s += ',';
                s += to_string(vec[k][j]);
                mp[s]++;
            }
            // Adding set size to our ans variable
            int cnt = mp.size();
            double ans = 0;
            // For all those, which were present in our array
            for (auto &e : mp)
            {
                double curr = (e.second - ((double)rows / ((double)levels[i] * levels[j]))) * (e.second - ((double)rows / ((double)levels[i] * levels[j])));
                ans += curr;
            }
            // For all those, which were not present in matrix
            for (int s = 0; s < (levels[i] * levels[j] - cnt); s++)
            {
                double curr = ((double)rows / (levels[i] * levels[j])) * ((double)rows / (levels[i] * levels[j]));
                ans += curr;
            }
            ans *= (((double)levels[i] * levels[j]) / (double)rows);
            // For two particular symbol ans will be our chi square value
            summaryTable[ans]++;
            chi_square_array[i][j] = ans;
            chi_square_array[j][i] = ans;
            final.push_back(ans);
            mp.clear();
        }
    }
}
// Utility Function For finding chiSqauareValueForSpecificIandJ
void chiSquareForIandJ(char i, char j, vector<vector<double>> &chi_square_array)
{
    // if (!isalpha(i) || !isalpha(j))
    // {
    //     cerr << "Please enter a valid value" << endl;
    //     return;
    // }
    int x = tolower(i);
    int y = tolower(j);
    x = x - 97;
    y = y - 97;
    cout << "Chi square value for (" << i << "," << j << ") is " << chi_square_array[x][y] << endl;
    return;
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
    
    double dos = DegreeOfSaturation(levels, rows);
    
    vector<vector<double>> chi_square_array;
    for (int i = 0; i < columns; i++)
    {
        vector<double> chi_square_row(columns, 0.00);
        chi_square_array.push_back(chi_square_row);
    }
    chi_square(vec, levels, chi_square_array);
    double output = 0;
    for (auto &e : final)
    {
        // cout << e << endl;
        output += e;
    }
    
    // output files
    ofstream fileOut;
    string output_filename;

    cout << "enter output file name: ";
    cin >> output_filename;

    fileOut.open(output_filename);
    fileOut << "Degree Of Saturation = " << dos;
    if(dos > 1){
        fileOut << ", the design is SUPER-SATURATED" << endl;
    }
    else if(dos <= 1){
        fileOut << ", the design is NOT super-satuturated" << endl;
    }
    fileOut << "Chi_square value for t=2 is " << output << endl;
    fileOut << "Chi_square - Frequency table: " << endl;
    fileOut << "Chi_square\t"
         << "|\tFrequency" << endl;
    fileOut << std::fixed;
    fileOut << setprecision(6);
    for (auto &e : summaryTable)
    {
        fileOut << e.first << "\t|\t" << e.second << endl;
    }
    auto min_value = summaryTable.begin();
    auto max_value = summaryTable.end();
    max_value--;
    fileOut << "Min chi_square_value in Design is " << min_value->first << endl;
    fileOut << "Max chi_square_value in Design is " << max_value->first << endl;
    fileOut << "chi_square Array: " << endl;
    for (int i = 0; i < chi_square_array.size(); i++)
    {
        for (int j = 0; j < chi_square_array[i].size(); j++)
        {
            fileOut << chi_square_array[i][j] << "\t";
        }
        fileOut << endl;
    }
    fileOut.close();
    char particular_chi;
    cout << "do you want to know the chi_sqauare value for any particular pair of columns - Y or N" << endl;
    cin >> particular_chi;
    if(particular_chi == 'Y'){
        char x;
        char y;
        cout << "enter the name of columns you want chi_square value for: " << endl;
        cin >> x >> y;
    chiSquareForIandJ(x, y, chi_square_array);
    }
    
    return 0;
}