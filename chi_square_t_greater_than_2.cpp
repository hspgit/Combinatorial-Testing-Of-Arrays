#include <bits/stdc++.h>
using namespace std;

unordered_map<string, double> mp;
map<string, double> chi_square_vals;
string curr = "";
double ans = 0.00;
// Using Brian Kerninghan algorithm to find number of set bits in a number
int countSetBits(int n)
{
    int count = 0;
    while (n)
    {
        n &= (n - 1);
        count++;
    }
    return count;
}

// Prints chi_square_values for a particular valid symbol combination
void print_chi_square_values_for_each_string()
{
    cout << setprecision(4) << endl;
    for (auto &e : chi_square_vals)
    {
        cout << e.first << "\t-\t" << e.second << endl;
    }
    return;
}

// Finds all valid patterns that can be possible whether it is present or not in design
void number_of_unique_strings_possible(int t, int n, vector<int> &levels, string curr1, string curr2, int i = 0, int cnt = 0)
{
    if (curr1.size() == t)
    {
        // if there are t symbols in the pattern, it means it is a valid pattern and make it frequency to 0
        string fn = curr1 + curr2;
        mp[fn] = 0;
        return;
    }
    if (i >= levels.size())
    {
        return;
    }
    // Finding all possible unique strings(symbols-level combination )
    number_of_unique_strings_possible(t, n, levels, curr1, curr2, i + 1, cnt);
    curr1 += 'a' + i;
    for (int j = 0; j < levels[i]; j++)
    {
        number_of_unique_strings_possible(t, n, levels, curr1, curr2 + to_string(j), i + 1, cnt + 1);
    }
}

void chi_square_for_each_unique_string(int t, int n, vector<int> &levels, int currLen = 0, double currAns = 1.00, int i = 0, string curr = "")
{
    if (currLen == t)
    {
        // if there are t symbols in the pattern, then updating the chi_square_value for that symbol combination
        chi_square_vals[curr] *= (double)currAns;
        chi_square_vals[curr] /= (double)n;
        ans += chi_square_vals[curr];
        return;
    }
    if (i >= levels.size())
    {
        return;
    }
    // we recurssively call for the function untill our currlen becomes equal to t or our index gets equal to our number of symbols/ levels.size()

    // For each symbol we have two choices, either to include or exclude it,
    //  if we include it our currlen will increase by 1 otherwise not
    chi_square_for_each_unique_string(t, n, levels, currLen, currAns, i + 1, curr);
    // Updating currAns which is equal to product of number of levels of symbols present in a particular pattern
    currAns *= (double)levels[i];
    curr += 'a' + i;
    chi_square_for_each_unique_string(t, n, levels, currLen + 1, currAns, i + 1, curr);
    return;
}

void update_frequency_of_string_in_design(vector<int> &vec, int t)
{
    int n = vec.size();
    for (int i = 1; i < (1 << n); ++i)
    {
        // if count of set bits in a number is not equal to t that means subsequence will not have t characters, and we don't need such subsequences
        if (countSetBits(i) != t)
        {
            continue;
        }
        // Forming two strings, curr1 having collection of symbols present and curr2 contains which level of a particular symbol is present
        string curr1 = "";
        string curr2 = "";
        for (int j = 0; j < n; ++j)
        {
            // jth bit is set in the i then we are adding jth index element of our vector in our subsequence
            if (i & (1 << j))
            {
                curr1 += 'a' + j;
                curr2 += to_string(vec[j]); // generate subsequence
            }
        }
        // Updating chi_square_value for particular symbols-level combination
        if (curr1.size() == t)
        {
            mp[curr1 + curr2]++;
        }
    }
    return;
}

void find_frequency_of_each_string(vector<int> &levels, int t, int rows)
{
    // Applying chi_square formula for each symbol-level pattern possible and updating chi_square_val for each valid symbol pattern
    for (auto &e : mp)
    {
        string key = e.first;
        string final_key = key.substr(0, t);
        double val = e.second;

        double levels_product = 1.00;
        for (int i = 0; i < final_key.size(); i++)
        {
            levels_product *= (double)levels[final_key[i] - 'a'];
        }
        chi_square_vals[final_key] += (val - ((double)rows / levels_product)) * (val - ((double)rows / levels_product));
    }
    return;
}
void number_of_unique_strings_in_design(vector<vector<int>> &vec, vector<int> &levels, int t)
{
    // For storing ans
    // Finding total number of rows in our array
    int rows = vec.size();
    for (auto &e : vec)
    {
        update_frequency_of_string_in_design(e, t);
    }
    find_frequency_of_each_string(levels, t, rows);
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
    string curr = "";
    number_of_unique_strings_possible(t, rows, levels, "", "", 0, 0);
    number_of_unique_strings_in_design(vec, levels, t);
    chi_square_for_each_unique_string(t, rows, levels, 0.00, 1.00, 0, "");
    print_chi_square_values_for_each_string();
    cout << setprecision(4) << endl;
    cout << "Total chi-square-value of design is " << ans << endl << endl;
    return 0;
}