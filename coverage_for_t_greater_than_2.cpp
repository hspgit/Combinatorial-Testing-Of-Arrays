#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <unordered_set>
#include <set>
using namespace std;

unordered_set<string> st;
long long denominator = 0;

// Using Brian Kerninghan algorithm to find number of set bits in a number
unsigned int countSetBits(int n)
{
    unsigned int count = 0;
    while (n)
    {
        n &= (n - 1);
        count++;
    }
    return count;
}

// Finding the total number of combinations possible for given t, levels and number of symbols and storing it in the answer
void findTotalNumberOfComb(int t, vector<int> levels, long long &ans, int currLen = 0, int currAns = 1, int i = 0)
{
    if (currLen == t)
    {
        ans += currAns;
        return;
    }
    if (i >= levels.size())
    {
        return;
    }
    // we recurssively call for the function untill our currlen becomes equal to t or our index gets equal to our number of symbols/ levels.size()

    // For each symbol we have two choices, either to include or exclude it,
    //  if we include it our currlen will increase by 1 otherwise not
    findTotalNumberOfComb(t, levels, ans, currLen, currAns, i + 1);
    currAns *= levels[i];
    findTotalNumberOfComb(t, levels, ans, currLen + 1, currAns, i + 1);
    return;
}
void findAllSubsequences(vector<int> &vec, int t)
{
    int n = vec.size();
    for (int i = 1; i < (1 << n); ++i)
    {
        // if count of set bits in a number is not equal to t that means subsequence will not have t characters, and we don't need such subsequences
        if (countSetBits(i) != t)
        {
            continue;
        }
        string subseq;

        for (int j = 0; j < n; ++j)
        {
            // jth bit is set in the i then we are adding jth index element of our vector in our subsequence
            if (i & (1 << j))
            {

                subseq += 'a' + j;
                subseq += to_string(vec[j]); // generate subsequence
            }
        }
        if (subseq.length() == 2 * t)
        {
            st.insert(subseq);
        }
    }
    return;
}

void TotalCombinationsCovered2(vector<vector<int>> &vec, vector<int> &levels, int t)
{
    // For storing ans
    // Finding total number of rows in our array
    int rows = vec.size();
    for (auto &e : vec)
    {
        findAllSubsequences(e, t);
    }

    return;
}

void printArray(vector<vector<int>> &vec, int rows, int columns)
{
    // Printing elements of the matrix
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < columns; j++)
        {
            cout << vec[i][j] << " ";
        }
        cout << endl;
    }
}
void printNumberOfRows(vector<vector<int>> &vec)
{
    cout << vec.size() << endl;
    return;
}
void printNumberOfColumns(vector<vector<int>> &vec)
{
    cout << vec[0].size() << endl;
    return;
}
int main()
{
    // taking filename as input from user
    string filename;
    cout << "Please enter the name of the input file." << endl;
    cin >> filename;
    int t;
    cout << "Enter the value of t for which testing is to be performed" << endl;
    cin >> t;
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

    // t can be from 2 to 6(even more), but time taken by the program will increase as we will increase our t
    // Time taken for t = 3 is around 44 seconds while for t = 6 is roughly 4-5 mins
    if (t > levels.size())
    {
        cerr << "Please enter the value of t in between 2 and number of symbols" << endl;
        return 1;
    }
    findTotalNumberOfComb(t, levels, denominator, 0, 1, 0);
    TotalCombinationsCovered2(vec, levels, t);
    int numerator = st.size();
    
    // Finding required ratio
    cout << filename << " has " << rows << " number of tests and " << columns << " parameters" << endl;
    cout << "Total unique Combinations possible = " << denominator << endl;
    cout << "Total combinations covered = " << numerator << endl;
    double coveringRatio = (double)numerator / denominator;
    cout << "Covering ratio = "<< coveringRatio << endl;
    return 0;
}