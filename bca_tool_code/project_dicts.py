import pandas as pd


class InputFileDict:
    """
    The InputFileDict class object contains a dictionary of the data provided via the input files for use throughout the tool.

    """
    def __init__(self, input_dict):
        self.input_dict = input_dict

    def create_project_dict(self, input_df, *args):
        """

        Parameters:
            input_df: DataFrame; contains data from the applicable input file.\n
            args: String(s); attributes to include in the returned dictionary key.

        Returns:
            The passed DataFrame as a dictionary with keys consisting of the passed args.

        """
        df = input_df.copy()
        cols = [arg for arg in args]
        len_cols = len(cols)
        if len_cols == 1: id = pd.Series(df[cols[0]])
        elif len_cols == 2: id = pd.Series(zip(df[cols[0]], df[cols[1]]))
        elif len_cols == 3: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]]), df[cols[2]]))
        elif len_cols == 4: id = pd.Series(zip(zip(df[cols[0]], df[cols[1]], df[cols[2]]), df[cols[3]]))
        else:
            print('Improper number of args passed to function.')
        df.insert(0, 'id', id)
        df.set_index('id', inplace=True)

        return df.to_dict('index')

    def get_attribute_value(self, key, attribute):
        """

        Parameters:
            key: Tuple; the key of the dictionary instance. \n
            attribute: String; represents the attribute to be updated.

        Returns:
            The value of 'attribute' within the dictionary instance.

        """
        value = self.input_dict[key][attribute]

        return value


if __name__ == '__main__':
    print('\nModule not meant to run as a script.')
