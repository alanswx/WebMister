import 'whatwg-fetch';
import React from 'react';
import { Item, Label, Table, Container, Header, Button } from 'semantic-ui-react';
import PropTypes from 'prop-types';

class Platform extends React.Component {
  constructor(props) {
    super(props);
  }



  render() {
    const { platform, releases } = this.props;

    let releaseList = releases ? releases.map((release) => {

      const {download_url, name, size, sha} = release;

      const humanSize = (size / 1000000).toFixed(2);
      return (
        <Table.Row>
          <Table.Cell>
            <Header as='h4'>
              <Header.Content>
                { name }
                <Header.Subheader>{ sha }</Header.Subheader>
              </Header.Content>
            </Header>
          </Table.Cell>
        <Table.Cell>
          <Button as="a" href={ download_url }>{`${humanSize}MB`}</Button>
        </Table.Cell>
        </Table.Row>
      );
    }) : null;

    return platform ? (
      <Container>
        <Item.Group divided>
          <Item>
            <Item.Content>
              <Item.Header as="a">{ platform.name }</Item.Header>
              <Item.Meta>
                <span>{ platform.repo }</span>
              </Item.Meta>
              <Item.Description>{ platform.branch }</Item.Description>
              <Item.Extra>
                <Label>{ platform.type }</Label>
                <Label>{ platform.additionalData ? 'Additional Data Required' : 'No Additional Data Required'}</Label>
              </Item.Extra>
            </Item.Content>
          </Item>
        </Item.Group>
        <Table basic='very'>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Release</Table.HeaderCell>
              <Table.HeaderCell>Download</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            { releaseList }
          </Table.Body>
        </Table>
      </Container>
    ) : null;
  }
}

Platform.propTypes = {
  platform: PropTypes.any.isRequired,
  releases: PropTypes.any.isRequired
};

export default Platform;
