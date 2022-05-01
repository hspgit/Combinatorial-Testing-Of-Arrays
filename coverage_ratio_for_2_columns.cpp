#include <iostream>
#include <iomanip>
#include <fstream>
#include <cctype>
#include <string>
#include <vector>
#include <algorithm>
#include <unordered_set>
#include <set>
using namespace std;

struct hashFunction
{
    size_t operator()(const pair<int, int> &x) const
    {
        return x.first ^ x.second;
    }
};

int findTotalUniqueCombinations(vector<int> &levels, int columns)
{

    // Initializing our TotalUniqueCombinations as 0
    int TotalUniqueCombinations = 0;
    // Checking for each possible pair (i, j) where i is the first column representing one symbol and j is the second column representing other symbol
    for (int i = 0; i < columns - 1; i++)
    {
        // for a particular we change the second symbol of the pair starting just to the right of the first symbol till last symbol
        for (int j = i + 1; j < columns; j++)
        {
            // Adding total combinations of particular pair(i, j) to our final ans where levels[i] and levels[j] represent number of levels for symbol i and j respectively
            TotalUniqueCombinations += levels[i] * levels[j];
        }
    }
    return TotalUniqueCombinations;
}

long long TotalCombinationsCovered(const vector<vector<int>> &vec, vector<int> &levels)
{
    // For storing ans
    long long ans = 0;
    // Finding total number of rows in our array
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

            // Making a unordered_set of strings to check for uniqueness
            unordered_set<string> st;
            // Checking for all rows for particular symbol pairs(i, j)
            for (int k = 0; k < rows; k++)
            {
                // Making a string of the form "(i,j)" and inserting into the set if it has been not covered yet
                string s = "";
                s += to_string(vec[k][i]);
                s += ',';
                s += to_string(vec[k][j]);
                st.insert(s);
            }
            // Adding set size to our ans variable
            ans += st.size();
            // Clearing the set
            st.clear();
        }
    }
    // Returning the Final ans
    return ans;
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
    // Initializing a  vector matrix having given rows and columns
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

    int den = findTotalUniqueCombinations(levels, columns);
    int num = TotalCombinationsCovered(vec, levels);
    cout << filename << " has " << rows << " number of tests and " << columns << " parameters" << endl;
    cout << "Total unique Combinations possible = " << den << endl;
    cout << "Total combinations covered = " << num << endl;
    double coveringRatio = (double)num / den;
    // Finding required ratio
    cout <<"Coverage ratio = " <<  coveringRatio << endl;
    return 0;
}